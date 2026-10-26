// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:desktop:viewmodel:v1
// Orchestrates the client: load packs, run the scenario text, save a receipt,
// verify a receipt file. Expected failures (CoreException, file errors) become
// the Status line; anything else propagates to the app's fail-closed handler.
// The file also holds the small MVVM plumbing the view model needs:
// ObservableObject (property change) and AsyncCommand (cancellable commands).

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Input;
using PfpLab.Client;

namespace PfpLab.Desktop;

public sealed class MainViewModel : ObservableObject, IDisposable
{
    private readonly IPfpLabClient _client;
    private string _scenarioJson = string.Empty;
    private string _status = "Starting the core...";
    private bool _statusIsError;
    private PackSummary? _selectedPack;
    private RunResult? _lastRun;

    public MainViewModel(IPfpLabClient client)
    {
        ArgumentNullException.ThrowIfNull(client);
        _client = client;
        RunCommand = new AsyncCommand(RunAsync, () => ScenarioJson.Length > 0);
    }

    public ObservableCollection<PackSummary> Packs { get; } = new();

    public ObservableCollection<Verdict> Verdicts { get; } = new();

    public AsyncCommand RunCommand { get; }

    public string ScenarioJson
    {
        get => _scenarioJson;
        set
        {
            if (Set(ref _scenarioJson, value ?? string.Empty))
            {
                RunCommand.RaiseCanExecuteChanged();
            }
        }
    }

    public PackSummary? SelectedPack
    {
        get => _selectedPack;
        set => Set(ref _selectedPack, value);
    }

    public string Status
    {
        get => _status;
        private set => Set(ref _status, value);
    }

    public bool StatusIsError
    {
        get => _statusIsError;
        private set => Set(ref _statusIsError, value);
    }

    public RunResult? LastRun
    {
        get => _lastRun;
        private set => Set(ref _lastRun, value);
    }

    public string Defect => LastRun?.Receipt.Final.Defect ?? "-";

    public string Obstruction => LastRun?.Receipt.Final.Obstruction ?? "-";

    public string Admitted => LastRun is null ? "-"
        : $"{LastRun.Receipt.Verdicts.Count(item => item.Admitted)}/{LastRun.Receipt.Verdicts.Count}";

    public string Digest => LastRun is null ? string.Empty : "receipt sha256 " + LastRun.Receipt.Digest;

    /// <summary>Show the core version and fill the pack list, then load the first pack.</summary>
    public async Task InitializeAsync(CancellationToken cancellationToken)
    {
        await Guard(async () =>
        {
            CoreVersion version = await _client.VersionAsync(cancellationToken);
            Packs.Clear();
            foreach (PackSummary pack in await _client.ListPacksAsync(cancellationToken))
            {
                Packs.Add(pack);
            }

            Report($"Core {version.Version} ready (AuthorityEffect: {version.AuthorityEffect}).", false);
        });
        if (Packs.Count > 0)
        {
            SelectedPack = Packs[0];
            await LoadSelectedPackAsync(cancellationToken);
        }
    }

    public async Task LoadSelectedPackAsync(CancellationToken cancellationToken)
    {
        if (SelectedPack is null)
        {
            return;
        }

        string packId = SelectedPack.PackId;
        await Guard(async () =>
        {
            ScenarioJson = await _client.GetPackJsonAsync(packId, cancellationToken);
            Report($"Loaded pack {packId}.", false);
        });
    }

    public async Task RunAsync(CancellationToken cancellationToken)
    {
        await Guard(async () =>
        {
            Show(await _client.RunAsync(ScenarioJson, cancellationToken));
            Report("Run complete. Every number shown was computed by the core.", false);
        });
    }

    public async Task SaveReceiptAsync(string path, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(path);
        if (LastRun is null)
        {
            Report("Run a scenario before saving its receipt.", true);
            return;
        }

        string text = LastRun.ReceiptJson + "\n";
        await Guard(async () =>
        {
            await File.WriteAllTextAsync(path, text, cancellationToken);
            Report($"Saved receipt to {path}.", false);
        });
    }

    public async Task VerifyFileAsync(string path, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(path);
        await Guard(async () =>
        {
            string text = await File.ReadAllTextAsync(path, cancellationToken);
            VerifyReport report = await _client.VerifyAsync(text, cancellationToken);
            string message = report.Valid
                ? $"Receipt verified: digest matches and replay agrees ({report.Digest})."
                : "Receipt NOT valid: " + string.Join("; ", report.Problems);
            Report(message, !report.Valid);
        });
    }

    private void Show(RunResult result)
    {
        LastRun = result;
        Verdicts.Clear();
        foreach (Verdict verdict in result.Receipt.Verdicts)
        {
            Verdicts.Add(verdict);
        }

        OnSummaryChanged();
    }

    private void OnSummaryChanged()
    {
        string[] names = [nameof(Defect), nameof(Obstruction), nameof(Admitted), nameof(Digest)];
        foreach (string name in names)
        {
            RaisePropertyChanged(name);
        }
    }

    private void Report(string message, bool isError)
    {
        Status = message;
        StatusIsError = isError;
    }

    private async Task Guard(Func<Task> action)
    {
        try
        {
            await action();
        }
        catch (CoreException error)
        {
            Report($"{error.Kind}: {error.Message}", true);
        }
        catch (OperationCanceledException)
        {
            Report("Cancelled.", true);
        }
        catch (IOException error)
        {
            Report("File error: " + error.Message, true);
        }
        catch (UnauthorizedAccessException error)
        {
            Report("File error: " + error.Message, true);
        }
    }

    public void Dispose()
    {
        RunCommand.Dispose();
    }
}

/// <summary>Minimal property-change plumbing for view models.</summary>
public abstract class ObservableObject : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;

    protected bool Set<T>(ref T field, T value, [CallerMemberName] string? name = null)
    {
        if (EqualityComparer<T>.Default.Equals(field, value))
        {
            return false;
        }

        field = value;
        RaisePropertyChanged(name);
        return true;
    }

    protected void RaisePropertyChanged(string? name)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}

public sealed class AsyncCommand : ICommand, IDisposable
{
    private readonly Func<CancellationToken, Task> _action;
    private readonly Func<bool> _canRun;
    private CancellationTokenSource? _running;

    public AsyncCommand(Func<CancellationToken, Task> action, Func<bool>? canRun = null)
    {
        ArgumentNullException.ThrowIfNull(action);
        _action = action;
        _canRun = canRun ?? (() => true);
    }

    public event EventHandler? CanExecuteChanged;

    public bool IsRunning => _running is not null;

    public bool CanExecute(object? parameter) => !IsRunning && _canRun();

    public async void Execute(object? parameter)
    {
        await RunAsync();
    }

    /// <summary>Run the action unless it is already running; exceptions propagate to the caller.</summary>
    public async Task RunAsync()
    {
        if (!CanExecute(null))
        {
            return;
        }

        using CancellationTokenSource source = new();
        _running = source;
        RaiseCanExecuteChanged();
        try
        {
            await _action(source.Token);
        }
        finally
        {
            _running = null;
            RaiseCanExecuteChanged();
        }
    }

    public void Cancel()
    {
        _running?.Cancel();
    }

    public void RaiseCanExecuteChanged()
    {
        CanExecuteChanged?.Invoke(this, EventArgs.Empty);
    }

    public void Dispose()
    {
        Cancel();
    }
}
