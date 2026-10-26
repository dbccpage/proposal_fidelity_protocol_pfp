// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:tests:viewmodel:v1
// The view model against a scripted client: no process, no window.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using PfpLab.Client;
using PfpLab.Desktop;

namespace PfpLab.Tests;

internal sealed class FakeClient : IPfpLabClient
{
    public CoreException? Failure { get; set; }

    public bool ReportValid { get; set; } = true;

    public bool NoPacks { get; set; }

    public List<string> Calls { get; } = [];

    public Task<CoreVersion> VersionAsync(CancellationToken cancellationToken) => Answer("version", new CoreVersion("9.9", "None"));

    public Task<IReadOnlyList<PackSummary>> ListPacksAsync(CancellationToken cancellationToken)
    {
        IReadOnlyList<PackSummary> packs = NoPacks ? [] : [new PackSummary("first", "First", 1), new PackSummary("second", "Second", 2)];
        return Answer("packs", packs);
    }

    public Task<string> GetPackJsonAsync(string packId, CancellationToken cancellationToken) => Answer("get " + packId, "{\"pack\":\"" + packId + "\"}");

    public Task<RunResult> RunAsync(string scenarioJson, CancellationToken cancellationToken)
    {
        Receipt receipt = JsonSerializer.Deserialize<Receipt>(UnitTests.SampleReceipt, JsonRpcChannel.WireOptions)
            ?? throw new TestFailure("sample");
        return Answer("run", new RunResult(receipt, "{\"receipt\":true}"));
    }

    public Task<VerifyReport> VerifyAsync(string receiptJson, CancellationToken cancellationToken)
    {
        return Answer("verify " + receiptJson, new VerifyReport(ReportValid, "abc", ReportValid ? [] : ["p1", "p2"]));
    }

    private Task<T> Answer<T>(string call, T value)
    {
        Calls.Add(call);
        return Failure is null ? Task.FromResult(value) : Task.FromException<T>(Failure);
    }
}

internal static class ViewModelTests
{
    public static IEnumerable<TestCase> All()
    {
        yield return new("view model loads packs and the first scenario", Initialize);
        yield return new("view model runs and summarises", RunAndSummary);
        yield return new("view model reports core failures", CoreFailure);
        yield return new("view model saves and verifies receipts", SaveAndVerify);
        yield return new("view model reports file errors", FileErrors);
        yield return new("async command disables itself and cancels", CommandBehaviour);
        yield return new("view model status text and error flag", StatusFlags);
    }

    private static async Task StatusFlags()
    {
        FakeClient client = new() { NoPacks = true };
        using MainViewModel model = new(client);
        int changes = 0;
        model.PropertyChanged += (_, e) => changes += e.PropertyName == nameof(MainViewModel.ScenarioJson) ? 1 : 0;
        model.ScenarioJson = "{}";
        model.ScenarioJson = "{}";
        Check.Equal(1, changes, "setting the same value raises no change");
        await model.InitializeAsync(CancellationToken.None);
        Check.Equal("Core 9.9 ready (AuthorityEffect: None).", model.Status, "version status");
        Check.True(!model.StatusIsError, "version status is not an error");
        await model.SaveReceiptAsync(Path.Combine(Path.GetTempPath(), "unused.json"), CancellationToken.None);
        Check.True(model.StatusIsError, "save before run is an error");
        await model.RunAsync(CancellationToken.None);
        Check.Equal("Run complete. Every number shown was computed by the core.", model.Status, "run status");
        Check.True(!model.StatusIsError, "run status is not an error");
        string path = Path.GetTempFileName();
        try
        {
            await model.SaveReceiptAsync(path, CancellationToken.None);
            Check.Equal($"Saved receipt to {path}.", model.Status, "save status");
            Check.True(!model.StatusIsError, "save status is not an error");
            using CancellationTokenSource cancelled = new();
            await cancelled.CancelAsync();
            await model.VerifyFileAsync(path, cancelled.Token);
            Check.True(model.StatusIsError, "cancelled is flagged");
            await model.VerifyFileAsync(path + ".missing", CancellationToken.None);
            Check.True(model.StatusIsError, "file error is flagged");
        }
        finally
        {
            File.Delete(path);
        }
    }

    private static async Task Initialize()
    {
        FakeClient client = new();
        using MainViewModel model = new(client);
        Check.True(!model.RunCommand.CanExecute(null), "nothing to run yet");
        await model.InitializeAsync(CancellationToken.None).ConfigureAwait(true);
        Check.Equal(2, model.Packs.Count, "packs");
        Check.Equal("first", model.SelectedPack?.PackId, "selected");
        Check.Equal("{\"pack\":\"first\"}", model.ScenarioJson, "scenario text");
        Check.Equal("Loaded pack first.", model.Status, "status");
        Check.True(!model.StatusIsError && model.RunCommand.CanExecute(null), "ready");
        model.SelectedPack = model.Packs[1];
        await model.LoadSelectedPackAsync(CancellationToken.None).ConfigureAwait(true);
        Check.Equal("{\"pack\":\"second\"}", model.ScenarioJson, "second scenario");
        model.SelectedPack = null;
        await model.LoadSelectedPackAsync(CancellationToken.None).ConfigureAwait(true);
        Check.Equal(4, client.Calls.Count, "no call without a selection");
    }

    private static async Task RunAndSummary()
    {
        using MainViewModel model = new(new FakeClient()) { ScenarioJson = "{}" };
        Check.Equal("-", model.Defect, "empty defect");
        Check.Equal("-", model.Admitted, "empty admitted");
        Check.Equal(string.Empty, model.Digest, "empty digest");
        List<string> changed = [];
        model.PropertyChanged += (_, e) => changed.Add(e.PropertyName ?? string.Empty);
        await model.RunCommand.RunAsync().ConfigureAwait(true);
        Check.Equal(1, model.Verdicts.Count, "verdicts");
        Check.Equal("1/2", model.Defect, "defect");
        Check.Equal("0", model.Obstruction, "obstruction");
        Check.Equal("1/1", model.Admitted, "admitted");
        Check.True(model.Digest.StartsWith("receipt sha256 0123", StringComparison.Ordinal), "digest");
        Check.True(changed.Contains("Defect") && changed.Contains("Digest"), "summary notified");
        model.ScenarioJson = null!;
        Check.Equal(string.Empty, model.ScenarioJson, "null text becomes empty");
    }

    private static async Task CoreFailure()
    {
        FakeClient client = new() { Failure = new CoreException(CoreErrorKind.Admission, "bad input") };
        using MainViewModel model = new(client) { ScenarioJson = "{}" };
        await model.InitializeAsync(CancellationToken.None).ConfigureAwait(true);
        Check.Equal("Admission: bad input", model.Status, "status");
        Check.True(model.StatusIsError, "error flag");
        Check.Equal(0, model.Packs.Count, "no packs");
        await model.RunAsync(CancellationToken.None).ConfigureAwait(true);
        Check.True(model.LastRun is null, "no run recorded");
    }

    private static async Task SaveAndVerify()
    {
        string folder = Path.Combine(Path.GetTempPath(), "pfp-vm-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(folder);
        try
        {
            FakeClient client = new();
            using MainViewModel model = new(client) { ScenarioJson = "{}" };
            string path = Path.Combine(folder, "r.json");
            await model.SaveReceiptAsync(path, CancellationToken.None).ConfigureAwait(true);
            Check.Equal("Run a scenario before saving its receipt.", model.Status, "save before run");
            await model.RunAsync(CancellationToken.None).ConfigureAwait(true);
            await model.SaveReceiptAsync(path, CancellationToken.None).ConfigureAwait(true);
            Check.Equal("{\"receipt\":true}\n", await File.ReadAllTextAsync(path).ConfigureAwait(true), "saved text");
            await model.VerifyFileAsync(path, CancellationToken.None).ConfigureAwait(true);
            Check.True(!model.StatusIsError && model.Status.Contains("verified", StringComparison.Ordinal), "valid");
            Check.Equal("verify {\"receipt\":true}\n", client.Calls[^1], "verify sent the file");
            client.ReportValid = false;
            await model.VerifyFileAsync(path, CancellationToken.None).ConfigureAwait(true);
            Check.Equal("Receipt NOT valid: p1; p2", model.Status, "invalid");
            Check.True(model.StatusIsError, "invalid flagged");
        }
        finally
        {
            Directory.Delete(folder, recursive: true);
        }
    }

    private static async Task FileErrors()
    {
        using MainViewModel model = new(new FakeClient()) { ScenarioJson = "{}" };
        string missing = Path.Combine(Path.GetTempPath(), "pfp-missing-" + Guid.NewGuid().ToString("N"), "x.json");
        await model.VerifyFileAsync(missing, CancellationToken.None).ConfigureAwait(true);
        Check.True(model.Status.StartsWith("File error:", StringComparison.Ordinal) && model.StatusIsError, "missing file");
        await model.RunAsync(CancellationToken.None).ConfigureAwait(true);
        await model.SaveReceiptAsync(missing, CancellationToken.None).ConfigureAwait(true);
        Check.True(model.Status.StartsWith("File error:", StringComparison.Ordinal), "unwritable path");
        using CancellationTokenSource cancelled = new();
        await cancelled.CancelAsync().ConfigureAwait(true);
        string real = Path.GetTempFileName();
        try
        {
            await model.VerifyFileAsync(real, cancelled.Token).ConfigureAwait(true);
            Check.Equal("Cancelled.", model.Status, "cancelled");
        }
        finally
        {
            File.Delete(real);
        }
    }

    private static async Task CommandBehaviour()
    {
        TaskCompletionSource release = new();
        CancellationToken seen = CancellationToken.None;
        using AsyncCommand command = new(async token =>
        {
            seen = token;
            await release.Task.ConfigureAwait(true);
        });
        int notifications = 0;
        command.CanExecuteChanged += (_, _) => notifications++;
        Check.True(command.CanExecute(null) && !command.IsRunning, "idle");
        Task running = command.RunAsync();
        Check.True(command.IsRunning && !command.CanExecute(null), "busy");
        await command.RunAsync().ConfigureAwait(true);
        command.Cancel();
        Check.True(seen.IsCancellationRequested, "token cancelled");
        release.SetResult();
        await running.ConfigureAwait(true);
        Check.True(!command.IsRunning && command.CanExecute(null), "idle again");
        Check.Equal(2, notifications, "two notifications");
        using AsyncCommand gated = new(_ => Task.CompletedTask, () => false);
        Check.True(!gated.CanExecute(null), "gate");
        Check.Throws<ArgumentNullException>(() => new AsyncCommand(null!), "null action");
        Check.Throws<ArgumentNullException>(() => new MainViewModel(null!), "null client");
    }
}
