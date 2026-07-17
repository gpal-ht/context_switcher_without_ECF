namespace ContextSwitcher.Work;

/// <summary>
/// A read-only, data-derived suggestion for planning the next session
/// (ADR-0018). Advisory only — the user acts on it; nothing is auto-applied.
/// Produced by <see cref="WorkSessionService.RecommendPlanning"/>.
/// </summary>
public sealed record PlanningRecommendation
{
    /// <summary>The project this recommendation is for.</summary>
    public required string Scope { get; init; }

    /// <summary>
    /// A suggested focus-timer length derived from recent sessions, or null
    /// when there is not enough history to suggest one.
    /// </summary>
    public TimeSpan? SuggestedFocus { get; init; }

    /// <summary>Plain-language basis for the suggested focus (always present).</summary>
    public required string SuggestedFocusReason { get; init; }

    /// <summary>
    /// The next action recorded in the most recent session that noted one, or
    /// null. The thing you said you'd do next.
    /// </summary>
    public string? PendingNextAction { get; init; }

    /// <summary>The project's most frequent recurring blocker, if any (a heads-up).</summary>
    public RecurringBlocker? TopBlocker { get; init; }
}
