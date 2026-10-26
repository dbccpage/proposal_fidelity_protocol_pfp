# PFP Lab for Windows (C#)

AuthorityEffect: None.

A WPF window over the Python core. The app does not reimplement the protocol:
it starts `python -m pfp_lab.cli.main stdio` and speaks JSON-RPC 2.0 to it, one
message per line, so every number on screen was computed by the same core the
command line and web page use. Rationals cross the boundary as canonical
strings and are held in `Rational` (parse, compare and print only).

| Project | Contents |
| --- | --- |
| `PfpLab.Client` | `Rational`, validated wire records, the JSON-RPC channel and `CoreException`, the child-process owner, the typed client |
| `PfpLab.Desktop` | The window, the view model with cancellable commands, and the app shell that owns the core process |
| `PfpLab.Tests` | Unit, view-model and contract tests in a small self-hosted runner |

## Build and run

Install the Python package first (see `pfp_lab/README.md`), then from the
repository root:

```powershell
dotnet build csharp/PfpLab.sln
dotnet run --project csharp/PfpLab.Desktop
dotnet run --project csharp/PfpLab.Tests
```

The app looks for `.venv\Scripts\python.exe` in the repository that holds
`pfp_lab`; set `PFP_LAB_PYTHON` to use another interpreter. The test runner
exits with 0 when every test passes and 3 when any fails; pass `--unit` to skip
the tests that start the Python core.

## Why a self-hosted test runner

This machine's NuGet source mapping admits `Microsoft.*` and a fixed list of
packages. The xUnit Visual Studio runner and SonarAnalyzer are not on it, so
the tests carry their own 100-line runner and the build uses only the .NET SDK
analyzers (warnings as errors, CA1502 cyclomatic limit 10, CA2000/CA1816
disposal, CA2016 cancellation). Nothing here changes the NuGet configuration.
