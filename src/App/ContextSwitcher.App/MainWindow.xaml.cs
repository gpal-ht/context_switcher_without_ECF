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
        TrySetWindowIcon();

        var store = new JsonFileWorkspaceStore();
        var projects = new ProjectRegistry(store);
        var sessions = new WorkSessionService(store);
        var knowledge = new KnowledgeService(store); // ADR-0024
        var todos = new NextActionService(store);    // ADR-0025
        _viewModel = new ShellViewModel(projects, sessions, knowledge, todos);
        Root.DataContext = _viewModel;

        _ticker = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
        _ticker.Tick += (_, _) => _viewModel.Tick();
        _ticker.Start();

        Closed += (_, _) => _ticker.Stop();
    }

    /// <summary>
    /// Sets the WinUI window/titlebar icon from the branded app.ico (ADR-0022).
    /// ApplicationIcon already covers the exe/taskbar; this ensures the titlebar
    /// too. Guarded — a missing icon is non-fatal.
    /// </summary>
    private void TrySetWindowIcon()
    {
        try
        {
            var icoPath = Path.Combine(AppContext.BaseDirectory, "Assets", "app.ico");
            if (File.Exists(icoPath))
            {
                AppWindow.SetIcon(icoPath);
            }
        }
        catch
        {
            // Icon is cosmetic; never let it break startup.
        }
    }
}
