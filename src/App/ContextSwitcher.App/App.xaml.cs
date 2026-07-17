using Microsoft.UI.Xaml;

namespace ContextSwitcher.App;

/// <summary>Application entry point for the Context Switcher WinUI 3 shell (ADR-0011).</summary>
public partial class App : Application
{
    private Window? _window;

    public App() => InitializeComponent();

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        _window = new MainWindow();
        _window.Activate();
    }
}
