using ContextSwitcher.App.ViewModels;
using ContextSwitcher.Work;
using Microsoft.UI.Xaml;

namespace ContextSwitcher.App;

/// <summary>
/// The shell window. Composition root for the GUI (ADR-0011): constructs the
/// store and services once and hands them to the view-model. A one-second
/// DispatcherTimer drives the focus-timer countdown (ADR-0012). The window
/// itself is an ordinary, closable desktop window (CLAUDE.md safety rules).
/// </summary>
public sealed partial class MainWindow : Window
{
    private readonly ShellViewModel _viewModel;
    private readonly DispatcherTimer _ticker;

    public MainWindow()
    {
        InitializeComponent();
        Title = "Context Switcher";

        var store = new JsonFileWorkspaceStore();
        var projects = new ProjectRegistry(store);
        var sessions = new WorkSessionService(store);
        _viewModel = new ShellViewModel(projects, sessions);
        Root.DataContext = _viewModel;

        _ticker = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
        _ticker.Tick += (_, _) => _viewModel.Tick();
        _ticker.Start();

        Closed += (_, _) => _ticker.Stop();
    }
}
