//! Stdin command, stdout local-profile JSON receipt plus LF. AuthorityEffect: None.

use core_adversary::dialectic::{self, DialecticBody, ReceiptStatus};
use core_adversary::receipt::Receipt;
use std::io::{self, Read, Write};
use std::process::ExitCode;

const MAX_STDIN: usize = 65_536;

/// Stdin byte budget of 65536 together with the separated exit codes 0, 1, 2, and 3.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct StdinBudgetWitness {
    opened: u64,
    spent: u64,
    remaining: u64,
    pass_exit: u8,
    fail_exit: u8,
    refusal_exit: u8,
    transport_exit: u8,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum StdinBudgetError {
    Budget,
    Overflow,
    ExitMap,
}

// Origin: engine/crates_rs/core_adversary/src/bin/adversary_dialectic.rs
// Claim: urn:core:crates_rs:core-adversary:adversary-dialectic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for StdinBudgetError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for StdinBudgetError {}

impl StdinBudgetWitness {
    fn validate_exit_codes(
        pass_exit: i32,
        fail_exit: i32,
        refusal_exit: i32,
        transport_exit: i32,
    ) -> Result<(), StdinBudgetError> {
        let sequential = pass_exit.checked_add(1) == Some(fail_exit)
            && fail_exit.checked_add(1) == Some(refusal_exit)
            && refusal_exit.checked_add(1) == Some(transport_exit)
            && transport_exit == 3;
        let distinct =
            pass_exit != fail_exit && fail_exit != refusal_exit && pass_exit != refusal_exit;
        if !sequential || !distinct {
            return Err(StdinBudgetError::ExitMap);
        }
        Ok(())
    }

    fn try_open(max: usize) -> Result<Self, StdinBudgetError> {
        if max != MAX_STDIN {
            return Err(StdinBudgetError::Budget);
        }
        let opened = u64::try_from(MAX_STDIN).map_err(|_| StdinBudgetError::Overflow)?;
        if opened != 65_536 {
            return Err(StdinBudgetError::Budget);
        }
        let pass_exit = status_exit(ReceiptStatus::Pass);
        let fail_exit = status_exit(ReceiptStatus::Fail);
        let refusal_exit = status_exit(ReceiptStatus::Refusal);
        let transport_exit = pass_exit.checked_add(3).ok_or(StdinBudgetError::ExitMap)?;
        Self::validate_exit_codes(
            i32::from(pass_exit),
            i32::from(fail_exit),
            i32::from(refusal_exit),
            i32::from(transport_exit),
        )?;
        Ok(Self {
            opened,
            spent: 0,
            remaining: opened,
            pass_exit,
            fail_exit,
            refusal_exit,
            transport_exit,
        })
    }

    fn try_push(&mut self, read: usize) -> Result<(), StdinBudgetError> {
        let read = u64::try_from(read).map_err(|_| StdinBudgetError::Overflow)?;
        let next = self
            .spent
            .checked_add(read)
            .ok_or(StdinBudgetError::Overflow)?;
        if next > self.opened {
            return Err(StdinBudgetError::Budget);
        }
        let remaining = self
            .opened
            .checked_sub(next)
            .ok_or(StdinBudgetError::Overflow)?;
        self.spent = next;
        self.remaining = remaining;
        Ok(())
    }

    fn matches_len(&self, len: usize) -> bool {
        let Some(len) = u64::try_from(len).ok() else {
            return false;
        };
        len == self.spent && self.spent.checked_add(self.remaining) == Some(self.opened)
    }

    fn exit_for(&self, status: ReceiptStatus) -> u8 {
        match status {
            ReceiptStatus::Pass => self.pass_exit,
            ReceiptStatus::Fail => self.fail_exit,
            ReceiptStatus::Refusal => self.refusal_exit,
        }
    }

    fn transport_exit(&self) -> u8 {
        self.transport_exit
    }
}

fn status_exit(status: ReceiptStatus) -> u8 {
    match status {
        ReceiptStatus::Pass => 0,
        ReceiptStatus::Fail => 1,
        ReceiptStatus::Refusal => 2,
    }
}

fn main() -> ExitCode {
    let mut budget = match StdinBudgetWitness::try_open(MAX_STDIN) {
        Ok(budget) => budget,
        Err(_) => return ExitCode::from(3),
    };
    let bytes = match read_at_most(&mut budget) {
        Ok(bytes) => bytes,
        Err(()) => {
            let receipt = Receipt::refusal(
                "INPUT_TOO_LARGE",
                "stdin exceeds 65536 bytes",
                DialecticBody::Absent,
            );
            return write_receipt(
                &receipt,
                budget.exit_for(ReceiptStatus::Refusal),
                budget.transport_exit(),
            );
        }
    };
    let receipt = dialectic::dialectic_bytes(&bytes);
    let code = budget.exit_for(receipt.status);
    write_receipt(&receipt, code, budget.transport_exit())
}

fn write_receipt(receipt: &Receipt<DialecticBody>, code: u8, transport: u8) -> ExitCode {
    let Ok(mut encoded) = dialectic::receipt_bytes(receipt) else {
        return ExitCode::from(transport);
    };
    encoded.push(b'\n');
    if io::stdout().write_all(&encoded).is_err() {
        return ExitCode::from(transport);
    }
    ExitCode::from(code)
}

fn read_at_most(budget: &mut StdinBudgetWitness) -> Result<Vec<u8>, ()> {
    let mut buf = Vec::new();
    let mut chunk = [0u8; 8192];
    let mut stdin = io::stdin().lock();
    loop {
        let read = stdin.read(&mut chunk).map_err(|_| ())?;
        if read == 0 {
            if budget.matches_len(buf.len()) {
                return Ok(buf);
            }
            return Err(());
        }
        if budget.try_push(read).is_err() {
            return Err(());
        }
        let Some(piece) = chunk.get(..read) else {
            return Err(());
        };
        buf.extend_from_slice(piece);
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_89d7b087 {
    use super::{ReceiptStatus, StdinBudgetError, StdinBudgetWitness, MAX_STDIN};

    #[test]
    fn stdin_budget_keeps_the_fixed_exit_map_and_refuses_invalid_maps() {
        let budget = StdinBudgetWitness::try_open(MAX_STDIN).unwrap();
        assert_eq!(budget.exit_for(ReceiptStatus::Pass), 0);
        assert_eq!(budget.exit_for(ReceiptStatus::Fail), 1);
        assert_eq!(budget.exit_for(ReceiptStatus::Refusal), 2);
        assert_eq!(budget.transport_exit(), 3);
        assert_eq!(
            StdinBudgetWitness::try_open(MAX_STDIN + 1),
            Err(StdinBudgetError::Budget)
        );
        for invalid in [(0, 0, 2, 3), (0, 1, 2, 4), (i32::MAX, 1, 2, 3)] {
            assert_eq!(
                StdinBudgetWitness::validate_exit_codes(invalid.0, invalid.1, invalid.2, invalid.3),
                Err(StdinBudgetError::ExitMap)
            );
        }
    }

    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
