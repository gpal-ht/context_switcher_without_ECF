namespace ContextSwitcher.Work;

/// <summary>
/// A ranked suggestion for which project to pick up next (ADR-0019). Advisory
/// only — the user switches projects themselves; nothing is auto-selected.
/// Produced by <see cref="WorkSessionService.SuggestNextProject"/>.
/// </summary>
public sealed record NextProjectSuggestion
{
    /// <summary>The candidate project's name.</summary>
    public required string Project { get; init; }

    /// <summary>True if this is the currently active project.</summary>
    public required bool IsActive { get; init; }

    /// <summary>When the project was most recently worked, or null if never.</summary>
    public DateTimeOffset? LastWorkedUtc { get; init; }

    /// <summary>The most recent recorded next action for the project, or null.</summary>
    public string? PendingNextAction { get; init; }

    /// <summary>Plain-language reason for the ranking.</summary>
    public required string Reason { get; init; }
}
