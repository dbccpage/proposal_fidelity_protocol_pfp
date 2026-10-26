// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:tests:contract:v1
// Contract tests against the real Python core, started as the app starts it.
// Receipts cross both ways: C# receipts verify with the Python CLI, and CLI
// receipts verify through the C# client. The C# records are also checked
// against the JSON Schema exported from the Pydantic models.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using PfpLab.Client;

namespace PfpLab.Tests;

internal static class ContractTests
{
    private static readonly CoreOptions Options = CoreOptions.Discover(AppContext.BaseDirectory, Environment.GetEnvironmentVariable("PFP_LAB_PYTHON"));

    public static IEnumerable<TestCase> All()
    {
        yield return new("core: version, packs and the Paper 005 session", PaperSession);
        yield return new("core: refusals map to typed kinds", Refusals);
        yield return new("core: C# receipt verifies with the Python CLI", CSharpToPython);
        yield return new("core: CLI receipt verifies through C#", PythonToCSharp);
        yield return new("core: a missing interpreter is a crash, not a hang", MissingInterpreter);
        yield return new("core: the process ends when disposed", Disposal);
        yield return new("records match the exported JSON Schema", SchemaMatches);
    }

    private static async Task<T> WithClient<T>(Func<PfpLabClient, Task<T>> body)
    {
        await using CoreProcess core = CoreProcess.Start(Options);
        PfpLabClient client = new(core.Channel, Options.CallTimeout);
        return await body(client).ConfigureAwait(false);
    }

    private static async Task PaperSession()
    {
        RunResult run = await WithClient(async client =>
        {
            CoreVersion version = await client.VersionAsync(CancellationToken.None).ConfigureAwait(false);
            Check.Equal("None", version.AuthorityEffect, "authority");
            IReadOnlyList<PackSummary> packs = await client.ListPacksAsync(CancellationToken.None).ConfigureAwait(false);
            Check.Equal("paper-005-worked-session", packs[0].PackId, "first pack");
            string scenario = await client.GetPackJsonAsync("paper-005-worked-session", CancellationToken.None).ConfigureAwait(false);
            Check.True(scenario.Contains("\n  \"schema\"", StringComparison.Ordinal), "pack JSON is indented for editing");
            return await client.RunAsync(scenario, CancellationToken.None).ConfigureAwait(false);
        }).ConfigureAwait(false);
        Verdict bad = run.Receipt.Verdicts[3];
        Check.True(!bad.Admitted && bad.Status == "DefectIncrease", "bad CUT refused");
        Check.Equal("3", bad.DefectBefore, "Phi_1 before");
        Check.Equal("5", bad.DefectAfter, "Phi_1 proposed");
        Check.Equal("ExactRepair", run.Receipt.Verdicts[4].Status, "repair");
        Check.Equal("3", run.Receipt.Final.Obstruction, "after retract");
    }

    private static async Task Refusals()
    {
        await WithClient(async client =>
        {
            CoreException unknown = await Check.ThrowsAsync<CoreException>(
                () => client.GetPackJsonAsync("nope", CancellationToken.None), "unknown pack").ConfigureAwait(false);
            Check.Equal(CoreErrorKind.UnknownPack, unknown.Kind, "unknown kind");
            CoreException refused = await Check.ThrowsAsync<CoreException>(
                () => client.RunAsync("{\"schema\":\"pfp-lab.scenario.v1\",\"vertices\":[],\"edges\":[],\"moves\":[]}", CancellationToken.None),
                "empty graph").ConfigureAwait(false);
            Check.Equal(CoreErrorKind.Admission, refused.Kind, "admission kind");
            CoreException local = await Check.ThrowsAsync<CoreException>(
                () => client.RunAsync("{oops", CancellationToken.None), "local json").ConfigureAwait(false);
            Check.Equal(CoreErrorKind.Admission, local.Kind, "local kind");
            VerifyReport forged = await client.VerifyAsync(Forged(), CancellationToken.None).ConfigureAwait(false);
            Check.True(!forged.Valid && forged.Problems.Count > 0, "forged receipt refused");
            return true;
        }).ConfigureAwait(false);
    }

    private static string Forged()
    {
        string text = RunCli("run", "--pack", "two-islands", "--json").Output;
        return text.Replace("\"obstruction\": \"0\"", "\"obstruction\": \"1\"", StringComparison.Ordinal);
    }

    private static async Task CSharpToPython()
    {
        RunResult run = await WithClient(async client =>
        {
            string scenario = await client.GetPackJsonAsync("refusal-gallery", CancellationToken.None).ConfigureAwait(false);
            return await client.RunAsync(scenario, CancellationToken.None).ConfigureAwait(false);
        }).ConfigureAwait(false);
        string path = Path.GetTempFileName();
        try
        {
            await File.WriteAllTextAsync(path, run.ReceiptJson + "\n", new UTF8Encoding(false)).ConfigureAwait(false);
            (int code, string output) = RunCli("verify", path);
            Check.Equal(0, code, "CLI exit code: " + output);
            Check.True(output.StartsWith("VALID  digest " + run.Receipt.Digest, StringComparison.Ordinal), "CLI verdict");
        }
        finally
        {
            File.Delete(path);
        }
    }

    private static async Task PythonToCSharp()
    {
        string receipt = RunCli("run", "--pack", "section-repair", "--json").Output;
        VerifyReport report = await WithClient(client => client.VerifyAsync(receipt, CancellationToken.None)).ConfigureAwait(false);
        Check.True(report.Valid && report.Problems.Count == 0, "C# verifies the CLI receipt");
    }

    private static async Task MissingInterpreter()
    {
        CoreOptions missing = Options with { PythonPath = Path.Combine(Path.GetTempPath(), "no-such-python.exe") };
        CoreException error = Check.Throws<CoreException>(() => CoreProcess.Start(missing), "missing interpreter");
        Check.Equal(CoreErrorKind.Crashed, error.Kind, "kind");
        CoreOptions wrong = Options with { WorkingDirectory = Path.GetTempPath(), PythonPath = "cmd.exe" };
        await using CoreProcess notPython = CoreProcess.Start(wrong);
        PfpLabClient client = new(notPython.Channel, TimeSpan.FromSeconds(10));
        CoreException crashed = await Check.ThrowsAsync<CoreException>(
            () => client.VersionAsync(CancellationToken.None), "not a core").ConfigureAwait(false);
        Check.True(crashed.Kind is CoreErrorKind.Protocol or CoreErrorKind.Crashed or CoreErrorKind.Timeout, "typed failure");
    }

    private static async Task Disposal()
    {
        CoreProcess core = CoreProcess.Start(Options);
        PfpLabClient client = new(core.Channel, Options.CallTimeout);
        await client.VersionAsync(CancellationToken.None).ConfigureAwait(false);
        Check.True(!core.HasExited, "running");
        await core.DisposeAsync().ConfigureAwait(false);
        await core.DisposeAsync().ConfigureAwait(false);
        Check.Equal(string.Empty, core.ErrorTail(), "quiet core");
    }

    private static Task SchemaMatches()
    {
        string schemaPath = Path.Combine(Options.WorkingDirectory, "contracts", "schema", "receipt.v1.schema.json");
        using JsonDocument schema = JsonDocument.Parse(File.ReadAllText(schemaPath));
        JsonElement root = schema.RootElement;
        JsonElement defs = root.GetProperty("$defs");
        CheckRecord(typeof(Receipt), root);
        CheckRecord(typeof(Verdict), defs.GetProperty("VerdictOut"));
        CheckRecord(typeof(FinalState), defs.GetProperty("StateOut"));
        CheckRecord(typeof(Claim), defs.GetProperty("ClaimIn"));
        return Task.CompletedTask;
    }

    private static void CheckRecord(Type record, JsonElement definition)
    {
        HashSet<string> required = definition.GetProperty("required").EnumerateArray().Select(item => item.GetString() ?? string.Empty).ToHashSet();
        HashSet<string> declared = record.GetProperties(BindingFlags.Public | BindingFlags.Instance)
            .Where(property => property.Name != "EqualityContract")
            .Select(property => JsonNamingPolicy.SnakeCaseLower.ConvertName(property.Name))
            .ToHashSet();
        Check.True(required.SetEquals(declared), $"{record.Name} fields {string.Join(",", declared)} vs schema {string.Join(",", required)}");
    }

    private static (int Code, string Output) RunCli(params string[] arguments)
    {
        ProcessStartInfo start = new(Options.PythonPath)
        {
            WorkingDirectory = Options.WorkingDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            StandardOutputEncoding = new UTF8Encoding(false),
        };
        start.ArgumentList.Add("-m");
        start.ArgumentList.Add("pfp_lab.cli.main");
        foreach (string argument in arguments)
        {
            start.ArgumentList.Add(argument);
        }

        using Process process = Process.Start(start) ?? throw new TestFailure("cannot start the CLI");
        string output = process.StandardOutput.ReadToEnd() + process.StandardError.ReadToEnd();
        process.WaitForExit();
        return (process.ExitCode, output);
    }
}
