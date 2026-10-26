// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:process:v1
// Owns the Python core child process (RULE_CS_003): starts it with a resolved
// interpreter, keeps the last lines of its error output for diagnostics, and on
// disposal closes its input, waits briefly, then kills the process tree.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace PfpLab.Client;

/// <summary>Where to find the Python core and how long to wait for it.</summary>
public sealed record CoreOptions(string PythonPath, string WorkingDirectory, TimeSpan CallTimeout)
{
    public static readonly TimeSpan DefaultCallTimeout = TimeSpan.FromSeconds(60);

    /// <summary>
    /// Find the repository that holds <c>pfp_lab</c> above <paramref name="start"/> and prefer its
    /// <c>.venv</c> interpreter. <c>PFP_LAB_PYTHON</c>, when set, names the interpreter instead.
    /// </summary>
    public static CoreOptions Discover(string start, string? pythonOverride)
    {
        ArgumentNullException.ThrowIfNull(start);
        DirectoryInfo? directory = new(start);
        while (directory is not null && !File.Exists(Path.Combine(directory.FullName, "pfp_lab", "__init__.py")))
        {
            directory = directory.Parent;
        }

        string root = directory?.FullName ?? start;
        string venvPython = Path.Combine(root, ".venv", "Scripts", "python.exe");
        string python = !string.IsNullOrWhiteSpace(pythonOverride) ? pythonOverride
            : File.Exists(venvPython) ? venvPython
            : "python";
        return new CoreOptions(python, root, DefaultCallTimeout);
    }
}

/// <summary>A running <c>python -m pfp_lab.cli.main stdio</c> and the channel to it.</summary>
public sealed class CoreProcess : IAsyncDisposable
{
    private const int KeptErrorLines = 40;
    private static readonly TimeSpan ExitGrace = TimeSpan.FromSeconds(5);

    private readonly Process _process;
    private readonly Queue<string> _errorTail = new();
    private readonly object _errorLock = new();
    private bool _disposed;

    private CoreProcess(Process process, CoreOptions options)
    {
        _process = process;
        Options = options;
        Channel = new JsonRpcChannel(process.StandardOutput, process.StandardInput, ErrorTail);
    }

    public CoreOptions Options { get; }

    public JsonRpcChannel Channel { get; }

    /// <summary>Start the core; a missing interpreter becomes <see cref="CoreErrorKind.Crashed"/>.</summary>
    public static CoreProcess Start(CoreOptions options)
    {
        ArgumentNullException.ThrowIfNull(options);
        ProcessStartInfo start = new(options.PythonPath)
        {
            WorkingDirectory = options.WorkingDirectory,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
            StandardInputEncoding = new UTF8Encoding(false),
            StandardOutputEncoding = new UTF8Encoding(false),
            StandardErrorEncoding = new UTF8Encoding(false),
        };
        start.ArgumentList.Add("-m");
        start.ArgumentList.Add("pfp_lab.cli.main");
        start.ArgumentList.Add("stdio");
        Process process = new() { StartInfo = start };
        try
        {
            process.Start();
        }
        catch (System.ComponentModel.Win32Exception error)
        {
            process.Dispose();
            throw new CoreException(CoreErrorKind.Crashed, $"cannot start '{options.PythonPath}': {error.Message}", null, error);
        }

        CoreProcess core = new(process, options);
        process.ErrorDataReceived += core.OnErrorLine;
        process.BeginErrorReadLine();
        return core;
    }

    public bool HasExited => _process.HasExited;

    private void OnErrorLine(object sender, DataReceivedEventArgs line)
    {
        if (line.Data is null)
        {
            return;
        }

        lock (_errorLock)
        {
            _errorTail.Enqueue(line.Data);
            while (_errorTail.Count > KeptErrorLines)
            {
                _errorTail.Dequeue();
            }
        }
    }

    /// <summary>The last lines the core wrote to its error stream, for crash reports.</summary>
    public string ErrorTail()
    {
        lock (_errorLock)
        {
            return _errorTail.Count == 0 ? string.Empty : Environment.NewLine + string.Join(Environment.NewLine, _errorTail.ToList());
        }
    }

    public async ValueTask DisposeAsync()
    {
        if (_disposed)
        {
            return;
        }

        _disposed = true;
        Channel.Dispose();
        await StopAsync().ConfigureAwait(false);
        _process.Dispose();
        GC.SuppressFinalize(this);
    }

    private async Task StopAsync()
    {
        if (_process.HasExited)
        {
            return;
        }

        try
        {
            _process.StandardInput.Close();
            using CancellationTokenSource grace = new(ExitGrace);
            await _process.WaitForExitAsync(grace.Token).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            _process.Kill(entireProcessTree: true);
        }
        catch (IOException)
        {
            _process.Kill(entireProcessTree: true);
        }
    }
}
