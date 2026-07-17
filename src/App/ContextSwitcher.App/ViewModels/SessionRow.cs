using ContextSwitcher.Work;

namespace ContextSwitcher.App.ViewModels;

/// <summary>
/// A history list entry: the underlying session plus its one-line summary
/// (ADR-0013). Selecting a row drives the detail pane.
/// </summary>
public sealed class SessionRow
{
    public required WorkSession Session { get; init; }
    public required string Summary { get; init; }
}
