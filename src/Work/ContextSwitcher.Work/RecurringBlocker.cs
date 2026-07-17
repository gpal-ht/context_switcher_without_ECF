namespace ContextSwitcher.Work;

/// <summary>
/// A blocker recorded across multiple sessions (ADR-0016). Pure data — produced
/// by <see cref="WorkSessionService.DetectRecurringBlockers"/>.
/// </summary>
public sealed record RecurringBlocker
{
    /// <summary>Representative text — the most recent original wording.</summary>
    public required string Text { get; init; }

    /// <summary>Number of sessions this blocker appeared in.</summary>
    public required int Count { get; init; }

    /// <summary>When the blocker was most recently recorded.</summary>
    public required DateTimeOffset LastSeenUtc { get; init; }
}
