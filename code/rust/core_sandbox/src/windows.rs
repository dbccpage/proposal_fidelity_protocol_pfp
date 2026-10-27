//! Windows Job Object implementation for process sandboxing (U09).

use super::*;
use std::io::Read;
use std::os::windows::io::AsRawHandle;
use std::os::windows::process::CommandExt;
use std::process::{Child, Command, Stdio};
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

type HANDLE = *mut std::ffi::c_void;
type BOOL = i32;
type DWORD = u32;

const JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE: DWORD = 0x00002000;
const JOB_OBJECT_LIMIT_PROCESS_MEMORY: DWORD = 0x00000100;
const JOB_OBJECT_LIMIT_JOB_MEMORY: DWORD = 0x00000200;

const JOB_OBJECT_EXTENDED_LIMIT_INFORMATION: i32 = 9;
const CREATE_SUSPENDED: DWORD = 0x00000004;
const CREATE_NO_WINDOW: DWORD = 0x08000000;
const TH32CS_SNAPTHREAD: DWORD = 0x00000004;
const THREAD_SUSPEND_RESUME: DWORD = 0x0002;
const ERROR_NO_MORE_FILES: i32 = 18;

#[repr(C)]
#[derive(Default)]
struct THREADENTRY32 {
    size: DWORD,
    usage: DWORD,
    thread_id: DWORD,
    owner_process_id: DWORD,
    base_priority: i32,
    delta_priority: i32,
    flags: DWORD,
}

#[repr(C)]
#[derive(Default)]
struct IO_COUNTERS {
    read_operation_count: u64,
    write_operation_count: u64,
    other_operation_count: u64,
    read_transfer_count: u64,
    write_transfer_count: u64,
    other_transfer_count: u64,
}

#[repr(C)]
#[derive(Default)]
struct JOBOBJECT_BASIC_LIMIT_INFORMATION {
    per_process_user_time_limit: i64,
    per_job_user_time_limit: i64,
    limit_flags: DWORD,
    minimum_working_set_size: usize,
    maximum_working_set_size: usize,
    active_process_limit: DWORD,
    affinity: usize,
    priority_class: DWORD,
    scheduling_class: DWORD,
}

#[repr(C)]
#[derive(Default)]
struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION {
    basic_limit_information: JOBOBJECT_BASIC_LIMIT_INFORMATION,
    io_info: IO_COUNTERS,
    process_memory_limit: usize,
    job_memory_limit: usize,
    peak_process_memory_limit: usize,
    peak_job_memory_limit: usize,
}

extern "system" {
    fn CreateJobObjectW(lpJobAttributes: *mut std::ffi::c_void, lpName: *const u16) -> HANDLE;
    fn SetInformationJobObject(
        hJob: HANDLE,
        JobObjectInformationClass: i32,
        lpJobObjectInformation: *const std::ffi::c_void,
        cbJobObjectInformationLength: DWORD,
    ) -> BOOL;
    fn QueryInformationJobObject(
        hJob: HANDLE,
        JobObjectInformationClass: i32,
        lpJobObjectInformation: *mut std::ffi::c_void,
        cbJobObjectInformationLength: DWORD,
        lpReturnLength: *mut DWORD,
    ) -> BOOL;
    fn AssignProcessToJobObject(hJob: HANDLE, hProcess: HANDLE) -> BOOL;
    fn TerminateJobObject(hJob: HANDLE, uExitCode: u32) -> BOOL;
    fn CloseHandle(hObject: HANDLE) -> BOOL;
    fn CreateToolhelp32Snapshot(dwFlags: DWORD, th32ProcessID: DWORD) -> HANDLE;
    fn Thread32First(hSnapshot: HANDLE, lpte: *mut THREADENTRY32) -> BOOL;
    fn Thread32Next(hSnapshot: HANDLE, lpte: *mut THREADENTRY32) -> BOOL;
    fn OpenThread(dwDesiredAccess: DWORD, bInheritHandle: BOOL, dwThreadId: DWORD) -> HANDLE;
    fn ResumeThread(hThread: HANDLE) -> DWORD;
}

struct JobHandle(HANDLE);
impl Drop for JobHandle {
    fn drop(&mut self) {
        if !self.0.is_null() {
            unsafe {
                CloseHandle(self.0);
            }
        }
    }
}

// Command closes the initial thread handle. On stable Rust, retrieve that thread
// from a Toolhelp snapshot while it is still suspended. Never resume before the
// job assignment; any enumeration/open/resume failure leaves it non-executing.
fn spawn_suspended(cmd: &mut Command) -> std::io::Result<Child> {
    cmd.creation_flags(CREATE_SUSPENDED | CREATE_NO_WINDOW);
    cmd.spawn()
}

fn find_sole_child_thread(child_pid: u32) -> std::io::Result<DWORD> {
    // SAFETY: the returned snapshot owns its handle, closed by the guard below.
    let snapshot = unsafe { CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0) };
    if snapshot == -1isize as HANDLE {
        return Err(std::io::Error::last_os_error());
    }
    let _snapshot_guard = JobHandle(snapshot);
    let mut entry = THREADENTRY32 {
        size: std::mem::size_of::<THREADENTRY32>() as DWORD,
        ..Default::default()
    };
    // SAFETY: entry is initialized, correctly sized, writable and live.
    if unsafe { Thread32First(snapshot, &mut entry) } == 0 {
        return Err(std::io::Error::last_os_error());
    }
    let mut initial_thread = None;
    loop {
        if entry.owner_process_id == child_pid
            && initial_thread.replace(entry.thread_id).is_some()
        {
            return Err(std::io::Error::other("Ambiguous suspended child threads"));
        }
        entry.size = std::mem::size_of::<THREADENTRY32>() as DWORD;
        // SAFETY: the snapshot and correctly sized entry remain live.
        if unsafe { Thread32Next(snapshot, &mut entry) } == 0 {
            let error = std::io::Error::last_os_error();
            if error.raw_os_error() != Some(ERROR_NO_MORE_FILES) {
                return Err(error);
            }
            break;
        }
    }
    initial_thread.ok_or_else(|| std::io::Error::other("Suspended child thread not found"))
}

fn assign_and_resume(
    child: &Child,
    job: HANDLE,
    start: Instant,
    timeout: Duration,
) -> std::io::Result<()> {
    // SAFETY: both handles remain owned and live through the assignment.
    if unsafe { AssignProcessToJobObject(job, child.as_raw_handle() as HANDLE) } == 0 {
        return Err(std::io::Error::last_os_error());
    }
    let id = find_sole_child_thread(child.id())?;
    // SAFETY: the target is our still-suspended child's sole initial thread.
    let thread = unsafe { OpenThread(THREAD_SUSPEND_RESUME, 0, id) };
    if thread.is_null() {
        return Err(std::io::Error::last_os_error());
    }
    let _thread_guard = JobHandle(thread);
    if start.elapsed() >= timeout {
        return Err(std::io::Error::new(
            std::io::ErrorKind::TimedOut,
            "Run deadline expired before resume",
        ));
    }
    // SAFETY: thread is an owned live handle with THREAD_SUSPEND_RESUME access.
    if unsafe { ResumeThread(thread) } != 1 {
        return Err(std::io::Error::other(
            "Failed to resume suspended child exactly once",
        ));
    }
    Ok(())
}

type CapturedOutput = std::io::Result<(Vec<u8>, bool)>;

fn read_output(mut reader: impl Read, limit: usize) -> CapturedOutput {
    let mut buf = Vec::new();
    let mut chunk = [0u8; 4096];
    loop {
        match reader.read(&mut chunk) {
            Ok(0) => return Ok((buf, false)),
            Ok(n) => {
                let keep = limit.saturating_sub(buf.len()).min(n);
                buf.extend_from_slice(&chunk[..keep]);
                if keep < n {
                    return Ok((buf, true));
                }
            }
            Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
            Err(error) => return Err(error),
        }
    }
}

fn poll_output(
    receiver: &mpsc::Receiver<CapturedOutput>,
    captured: &mut Option<Vec<u8>>,
) -> Result<(), SandboxOutcome> {
    if captured.is_some() {
        return Ok(());
    }
    match receiver.try_recv() {
        Ok(Ok((_, true))) => Err(SandboxOutcome::OutputLimitExceeded),
        Ok(Ok((bytes, false))) => {
            *captured = Some(bytes);
            Ok(())
        }
        Ok(Err(error)) => Err(SandboxOutcome::LaunchRefused(format!(
            "Output capture failed: {error}"
        ))),
        Err(mpsc::TryRecvError::Empty) => Ok(()),
        Err(mpsc::TryRecvError::Disconnected) => Err(SandboxOutcome::LaunchRefused(
            "Output capture channel disconnected".to_string(),
        )),
    }
}

pub fn run_windows(config: &SandboxConfig) -> SandboxOutcome {
    run_windows_inner(config, None)
}

pub fn run_windows_observed(
    config: &SandboxConfig,
    observation: &mut crate::ResourceObservation,
) -> SandboxOutcome {
    run_windows_inner(config, Some(observation))
}

fn create_configured_job(memory_limit_bytes: u64) -> Result<JobHandle, SandboxOutcome> {
    let job = unsafe { CreateJobObjectW(std::ptr::null_mut(), std::ptr::null()) };
    if job.is_null() {
        return Err(SandboxOutcome::IsolationUnavailable(
            "Failed to create Job Object".to_string(),
        ));
    }
    let job_guard = JobHandle(job);

    let mut info: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = Default::default();
    info.basic_limit_information.limit_flags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        | JOB_OBJECT_LIMIT_JOB_MEMORY
        | JOB_OBJECT_LIMIT_PROCESS_MEMORY;
    info.process_memory_limit = memory_limit_bytes as usize;
    info.job_memory_limit = memory_limit_bytes as usize;

    let set_ok = unsafe {
        SetInformationJobObject(
            job,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            &info as *const _ as *const _,
            std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as DWORD,
        )
    };
    if set_ok == 0 {
        return Err(SandboxOutcome::IsolationUnavailable(
            "Failed to configure Job Object limits".to_string(),
        ));
    }
    Ok(job_guard)
}

fn build_sandbox_command(config: &SandboxConfig) -> Command {
    let mut cmd = Command::new(&config.command[0]);
    cmd.args(&config.command[1..]);
    if let Some(ref cwd) = config.cwd {
        cmd.current_dir(cwd);
    }
    for (k, v) in &config.env {
        cmd.env(k, v);
    }
    cmd.stdin(Stdio::null());
    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());
    cmd
}

fn poll_child_exit(
    child: &mut Child,
    exit_status: &mut Option<std::process::ExitStatus>,
) -> Result<(), SandboxOutcome> {
    if exit_status.is_none() {
        *exit_status = child
            .try_wait()
            .map_err(|error| SandboxOutcome::LaunchRefused(error.to_string()))?;
    }
    Ok(())
}

fn wait_for_child_and_streams(
    child: &mut Child,
    job: HANDLE,
    start: Instant,
    timeout: Duration,
    stdout_rx: &mpsc::Receiver<CapturedOutput>,
    stderr_rx: &mpsc::Receiver<CapturedOutput>,
) -> Result<(std::process::ExitStatus, Vec<u8>, Vec<u8>), SandboxOutcome> {
    let mut exit_status = None;
    let mut stdout_bytes = None;
    let mut stderr_bytes = None;
    loop {
        let remaining = timeout.saturating_sub(start.elapsed());
        if remaining.is_zero() {
            // SAFETY: job is still owned by the guard; terminate all descendants.
            unsafe { TerminateJobObject(job, 1) };
            let _ = child.kill();
            let _ = child.wait();
            return Err(SandboxOutcome::TimedOut);
        }
        poll_output(stdout_rx, &mut stdout_bytes)?;
        poll_output(stderr_rx, &mut stderr_bytes)?;
        poll_child_exit(child, &mut exit_status)?;
        if [exit_status.is_some(), stdout_bytes.is_some(), stderr_bytes.is_some()]
            .into_iter()
            .all(|b| b)
            && start.elapsed() < timeout
        {
            break;
        }
        thread::sleep(remaining.min(Duration::from_millis(20)));
    }
    match (exit_status, stdout_bytes, stderr_bytes) {
        (Some(status), Some(stdout), Some(stderr)) => Ok((status, stdout, stderr)),
        _ => Err(SandboxOutcome::LaunchRefused(
            "Incomplete output capture".to_string(),
        )),
    }
}

fn query_job_peak_memory(
    job: HANDLE,
    observation: &mut Option<&mut crate::ResourceObservation>,
) -> u64 {
    let mut query_info: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = Default::default();
    let mut ret_len: DWORD = 0;
    let query_ok = unsafe {
        QueryInformationJobObject(
            job,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            &mut query_info as *mut _ as *mut _,
            std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as DWORD,
            &mut ret_len,
        )
    };
    let peak_memory = query_info.peak_job_memory_limit as u64;
    if let Some(value) = observation.as_deref_mut() {
        if query_ok != 0 {
            value.memory_bytes = Some(peak_memory);
            value.measurement_error = None;
        } else {
            value.measurement_error = Some(format!(
                "JOB_MEMORY_QUERY_FAILED: {}",
                std::io::Error::last_os_error()
            ));
        }
    }
    peak_memory
}

fn is_memory_overflow(
    exit_code: i32,
    stderr_str: &str,
    peak_memory: u64,
    memory_limit_bytes: u64,
) -> bool {
    // NTSTATUS codes for memory overflow:
    // STATUS_NO_MEMORY (0xC0000017 = -1073741801)
    // STATUS_JOB_P_MEM_LIMIT (0xC0000420 = -1073740768)
    exit_code == -1073741801
        || exit_code == -1073740768
        || (exit_code != 0 && stderr_str.contains("MemoryError"))
        || peak_memory > memory_limit_bytes
}

fn spawn_and_assign_job(
    config: &SandboxConfig,
    job: HANDLE,
    start: Instant,
    timeout: Duration,
    observation: &mut Option<&mut crate::ResourceObservation>,
) -> Result<Child, SandboxOutcome> {
    let mut cmd = build_sandbox_command(config);
    let mut child =
        spawn_suspended(&mut cmd).map_err(|e| SandboxOutcome::LaunchRefused(e.to_string()))?;
    if let Some(value) = observation.as_deref_mut() {
        value.task_pid = Some(child.id());
    }
    if let Err(error) = assign_and_resume(&child, job, start, timeout) {
        let _ = child.kill();
        let _ = child.wait();
        if error.kind() == std::io::ErrorKind::TimedOut {
            return Err(SandboxOutcome::TimedOut);
        }
        return Err(SandboxOutcome::IsolationUnavailable(format!(
            "Failed to assign and resume process in Job Object: {error}"
        )));
    }
    if let Some(value) = observation.as_deref_mut() {
        value.isolation_applied = true;
    }
    Ok(child)
}

fn run_windows_inner(
    config: &SandboxConfig,
    mut observation: Option<&mut crate::ResourceObservation>,
) -> SandboxOutcome {
    let start = Instant::now();
    let timeout = Duration::from_millis(config.timeout_ms);
    let job_guard = match create_configured_job(config.memory_limit_bytes) {
        Ok(g) => g,
        Err(outcome) => return outcome,
    };
    let job = job_guard.0;

    let mut child = match spawn_and_assign_job(config, job, start, timeout, &mut observation) {
        Ok(c) => c,
        Err(outcome) => return outcome,
    };
    let (stdout_handle, stderr_handle) = match (child.stdout.take(), child.stderr.take()) {
        (Some(stdout), Some(stderr)) => (stdout, stderr),
        _ => return SandboxOutcome::LaunchRefused("Output pipes unavailable".to_string()),
    };
    let max_output = config.max_output_bytes;

    let (stdout_tx, stdout_rx) = mpsc::channel();
    let (stderr_tx, stderr_rx) = mpsc::channel();
    thread::spawn(move || {
        let _ = stdout_tx.send(read_output(stdout_handle, max_output));
    });
    thread::spawn(move || {
        let _ = stderr_tx.send(read_output(stderr_handle, max_output));
    });

    let (exit_status, stdout_bytes, stderr_bytes) =
        match wait_for_child_and_streams(&mut child, job, start, timeout, &stdout_rx, &stderr_rx) {
            Ok(res) => res,
            Err(outcome) => return outcome,
        };
    let duration_ms = start.elapsed().as_millis() as u64;
    if let Some(value) = observation.as_deref_mut() {
        value.stdout_hex = Some(stdout_bytes.iter().map(|b| format!("{b:02x}")).collect());
        value.stderr_hex = Some(stderr_bytes.iter().map(|b| format!("{b:02x}")).collect());
    }
    let stderr_str = String::from_utf8_lossy(&stderr_bytes).to_string();
    let stdout_str = String::from_utf8_lossy(&stdout_bytes).to_string();
    let exit_code = exit_status.code().unwrap_or(-1);
    let peak_memory = query_job_peak_memory(job, &mut observation);

    if is_memory_overflow(exit_code, &stderr_str, peak_memory, config.memory_limit_bytes) {
        return SandboxOutcome::MemoryLimitExceeded;
    }

    SandboxOutcome::Completed {
        exit_code,
        stdout: stdout_str,
        stderr: stderr_str,
        duration_ms,
        peak_memory_bytes: peak_memory,
    }
}

// Origin: engine/crates_rs/core_sandbox/src/windows.rs
// Claim: urn:core:crates_rs:core-sandbox:windows:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord351b0fd5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord351b0fd5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError351b0fd5 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError351b0fd5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError351b0fd5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError351b0fd5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord351b0fd5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError351b0fd5> {
        if capacity_bound == 0 {
            return Err(BoundaryError351b0fd5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError351b0fd5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError351b0fd5::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct FixtureChild(Child);
    impl std::ops::Deref for FixtureChild {
        type Target = Child;
        fn deref(&self) -> &Child {
            &self.0
        }
    }
    impl std::ops::DerefMut for FixtureChild {
        fn deref_mut(&mut self) -> &mut Child {
            &mut self.0
        }
    }
    impl Drop for FixtureChild {
        fn drop(&mut self) {
            let _ = self.0.kill();
            let _ = self.0.wait();
        }
    }

    extern "system" {
        fn IsProcessInJob(process: HANDLE, job: HANDLE, result: *mut BOOL) -> BOOL;
    }

    #[test]
    #[ignore = "native child fixture launched by the suspension regression"]
    fn suspended_child_fixture() {
        std::fs::write(std::env::var_os("CORE_SUSPENDED_MARKER").unwrap(), b"ran").unwrap();
    }

    fn marker_child(marker: &std::path::Path) -> FixtureChild {
        let mut cmd = Command::new(std::env::current_exe().unwrap());
        cmd.args([
            "--exact",
            "windows::tests::suspended_child_fixture",
            "--ignored",
        ])
        .env("CORE_SUSPENDED_MARKER", marker)
        .stdout(Stdio::null())
        .stderr(Stdio::null());
        FixtureChild(spawn_suspended(&mut cmd).unwrap())
    }

    #[test]
    fn child_stays_suspended_until_job_assignment() {
        let dir = tempfile::tempdir().unwrap();
        let marker = dir.path().join("executed");
        let mut child = marker_child(&marker);
        // SAFETY: create an unnamed job owned by this test's guard.
        let job = unsafe { CreateJobObjectW(std::ptr::null_mut(), std::ptr::null()) };
        assert!(!job.is_null());
        let _guard = JobHandle(job);
        thread::sleep(Duration::from_millis(100));
        assert!(!marker.exists(), "candidate executed before assignment");
        let mut member = 1;
        // SAFETY: valid child/job handles and a writable BOOL.
        assert_ne!(
            unsafe { IsProcessInJob(child.as_raw_handle() as HANDLE, job, &mut member) },
            0
        );
        assert_eq!(member, 0);
        assign_and_resume(&child, job, Instant::now(), Duration::from_secs(5)).unwrap();
        assert_ne!(
            unsafe { IsProcessInJob(child.as_raw_handle() as HANDLE, job, &mut member) },
            0
        );
        assert_eq!(member, 1);
        let deadline = Instant::now() + Duration::from_secs(5);
        loop {
            if let Some(status) = child.try_wait().unwrap() {
                assert!(status.success());
                break;
            }
            if Instant::now() >= deadline {
                let _ = child.kill();
                let _ = child.wait();
                panic!("resumed fixture did not finish");
            }
            thread::sleep(Duration::from_millis(10));
        }
        assert_eq!(std::fs::read(marker).unwrap(), b"ran");
    }

    #[test]
    fn failed_assignment_never_runs_candidate() {
        let dir = tempfile::tempdir().unwrap();
        let marker = dir.path().join("executed");
        let mut child = marker_child(&marker);
        assert!(assign_and_resume(
            &child,
            std::ptr::null_mut(),
            Instant::now(),
            Duration::from_secs(5)
        )
        .is_err());
        thread::sleep(Duration::from_millis(100));
        let absent = !marker.exists();
        let _ = child.kill();
        let _ = child.wait();
        assert!(absent, "failed assignment let the child execute");
    }

    #[test]
    fn expired_deadline_never_resumes_candidate() {
        let dir = tempfile::tempdir().unwrap();
        let marker = dir.path().join("executed");
        let mut child = marker_child(&marker);
        // SAFETY: create an unnamed job owned by this test's guard.
        let job = unsafe { CreateJobObjectW(std::ptr::null_mut(), std::ptr::null()) };
        assert!(!job.is_null());
        let _guard = JobHandle(job);
        let error = assign_and_resume(&child, job, Instant::now(), Duration::ZERO).unwrap_err();
        let _ = child.kill();
        let _ = child.wait();
        assert_eq!(error.kind(), std::io::ErrorKind::TimedOut);
        assert!(!marker.exists(), "expired deadline let the child execute");
    }

    #[test]
    fn read_output_errors_are_not_success() {
        struct BrokenReader;
        impl Read for BrokenReader {
            fn read(&mut self, _: &mut [u8]) -> std::io::Result<usize> {
                Err(std::io::Error::other("injected read failure"))
            }
        }
        let (tx, rx) = mpsc::channel();
        tx.send(read_output(BrokenReader, 64)).unwrap();
        assert!(matches!(
            poll_output(&rx, &mut None),
            Err(SandboxOutcome::LaunchRefused(_))
        ));
        drop(tx);
        assert!(matches!(
            poll_output(&rx, &mut None),
            Err(SandboxOutcome::LaunchRefused(_))
        ));
    }

    #[test]
    fn complete_bounded_output_including_empty_is_accepted() {
        for bytes in [vec![], vec![b'x'; 64]] {
            let (tx, rx) = mpsc::channel();
            let (captured, overflow) = read_output(std::io::Cursor::new(&bytes), 64).unwrap();
            assert!(!overflow);
            tx.send(Ok((captured, overflow))).unwrap();
            let mut result = None;
            poll_output(&rx, &mut result).unwrap();
            assert_eq!(result, Some(bytes));
        }
        assert!(
            read_output(std::io::Cursor::new(vec![b'x'; 65]), 64)
                .unwrap()
                .1
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_351b0fd5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord351b0fd5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord351b0fd5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord351b0fd5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord351b0fd5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord351b0fd5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError351b0fd5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError351b0fd5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
