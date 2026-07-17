namespace ContextSwitcher.Work;

/// <summary>
/// A derived focus-trends summary over closed sessions for a scope (one project
/// or the whole workspace). Pure data — computed by
/// <see cref="WorkSessionService.ComputeInsights"/> (ADR-0015).
/// </summary>
public sealed record FocusInsights
{
    /// <summary>Human-readable scope, e.g. "all projects" or a project name.</summary>
    public required string Scope { get; init; }

    /// <summary>Number of closed sessions considered.</summary>
    public required int SessionCount { get; init; }

    /// <summary>Total focused time across the closed sessions.</summary>
    public required TimeSpan TotalFocus { get; init; }

    /// <summary>Mean session length, or null when there are no sessions.</summary>
    public TimeSpan? AverageFocus { get; init; }

    /// <summary>Count of sessions per outcome.</summary>
    public required IReadOnlyDictionary<SessionOutcome, int> OutcomeCounts { get; init; }

    /// <summary>Number of closed sessions that had a focus timer.</summary>
    public required int TimedCount { get; init; }

    /// <summary>How many timed sessions ran over their plan.</summary>
    public required int OverranCount { get; init; }

    /// <summary>
    /// Mean signed overrun across timed sessions (positive = tended to run
    /// over, negative = tended to finish early), or null when none were timed.
    /// </summary>
    public TimeSpan? AverageOverrun { get; init; }

    /// <summary>Focused time in the last 7 days.</summary>
    public required TimeSpan RecentFocus { get; init; }

    /// <summary>Focused time in the 7 days before the last 7.</summary>
    public required TimeSpan PriorFocus { get; init; }

    /// <summary>Fraction of sessions whose outcome was <see cref="SessionOutcome.Completed"/>.</summary>
    public double CompletionRate =>
        SessionCount == 0
            ? 0
            : OutcomeCounts.GetValueOrDefault(SessionOutcome.Completed) / (double)SessionCount;

    /// <summary>+1 if recent focus exceeds the prior week, -1 if less, 0 if equal.</summary>
    public int TrendDirection => RecentFocus.CompareTo(PriorFocus);
}
