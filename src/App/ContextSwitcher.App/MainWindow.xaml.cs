using ContextSwitcher.App.ViewModels;
using ContextSwitcher.Work;
using Microsoft.UI.Xaml;

namespace ContextSwitcher.App;

/// <summary>
/// The shell window. Composition root for the GUI (ADR-0011): constructs the
/// store and services once and hands them to the view-model. The window itself
/// is an ordinary, closable desktop window (CLAUDE.md safety rules).
/// </summary>
public sealed partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        Title = "Context Switcher";

        var store = new JsonFileWorkspaceStore();
        var projects = new ProjectRegistry(store);
        var sessions = new WorkSessionService(store);
        Root.DataContext = new ShellViewModel(projects, sessions);
    }
}
