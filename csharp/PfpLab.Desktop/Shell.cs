// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:desktop:shell:v1
// The application shell. App starts the Python core, opens the window and
// closes the core on exit; an unexpected exception is shown and ends the app
// (fail-closed), so the window never keeps showing results it can no longer
// vouch for. MainWindow is view wiring only: file dialogs, pack selection and
// status colour; closing it cancels whatever the view model is waiting on.

using System;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;
using Microsoft.Win32;
using PfpLab.Client;

namespace PfpLab.Desktop;

public partial class App : Application
{
    private CoreProcess? _core;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        DispatcherUnhandledException += OnUnhandled;
        CoreOptions options = CoreOptions.Discover(AppContext.BaseDirectory, Environment.GetEnvironmentVariable("PFP_LAB_PYTHON"));
        try
        {
            _core = CoreProcess.Start(options);
        }
        catch (CoreException error)
        {
            MessageBox.Show(error.Message + "\n\nSet PFP_LAB_PYTHON to a Python with pfp_lab installed.", "PFP Lab");
            Shutdown(1);
            return;
        }

        PfpLabClient client = new(_core.Channel, options.CallTimeout);
        MainWindow window = new(new MainViewModel(client));
        window.Show();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        CoreProcess? core = _core;
        _core = null;
        if (core is not null)
        {
            Task.Run(async () => await core.DisposeAsync().ConfigureAwait(false)).GetAwaiter().GetResult();
        }

        base.OnExit(e);
    }

    private void OnUnhandled(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        e.Handled = true;
        MessageBox.Show("PFP Lab stopped after an unexpected error:\n\n" + e.Exception, "PFP Lab");
        Shutdown(2);
    }
}

[SuppressMessage("Reliability", "CA1001", Justification = "WPF owns the window's lifetime; OnClosed disposes the token source.")]
public partial class MainWindow : Window
{
    private const string ReceiptFilter = "Receipt JSON (*.json)|*.json";
    private readonly MainViewModel _model;
    private readonly CancellationTokenSource _closing = new();

    public MainWindow(MainViewModel model)
    {
        ArgumentNullException.ThrowIfNull(model);
        InitializeComponent();
        _model = model;
        DataContext = model;
        model.PropertyChanged += OnModelChanged;
        Loaded += async (_, _) => await _model.InitializeAsync(_closing.Token);
    }

    private async void OnPackChanged(object sender, SelectionChangedEventArgs e)
    {
        if (e.AddedItems.Count > 0 && PackBox.IsLoaded)
        {
            await _model.LoadSelectedPackAsync(_closing.Token);
        }
    }

    private async void OnSave(object sender, RoutedEventArgs e)
    {
        SaveFileDialog dialog = new() { Filter = ReceiptFilter, FileName = "pfp-receipt.json" };
        if (dialog.ShowDialog(this) == true)
        {
            await _model.SaveReceiptAsync(dialog.FileName, _closing.Token);
        }
    }

    private async void OnVerify(object sender, RoutedEventArgs e)
    {
        OpenFileDialog dialog = new() { Filter = ReceiptFilter };
        if (dialog.ShowDialog(this) == true)
        {
            await _model.VerifyFileAsync(dialog.FileName, _closing.Token);
        }
    }

    private void OnModelChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(MainViewModel.StatusIsError))
        {
            StatusLine.Foreground = _model.StatusIsError ? (Brush)FindResource("Refused") : SystemColors.ControlTextBrush;
        }
    }

    protected override void OnClosing(CancelEventArgs e)
    {
        _closing.Cancel();
        _model.Dispose();
        base.OnClosing(e);
    }

    protected override void OnClosed(EventArgs e)
    {
        _closing.Dispose();
        base.OnClosed(e);
    }
}
