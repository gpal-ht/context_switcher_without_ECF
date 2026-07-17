using System.Text.Json.Serialization;

namespace ContextSwitcher.Work;

/// <summary>
/// The single outcome every work session ends with (WORK_SESSION_MODEL.md).
/// All outcomes are valid; the objective is to preserve learning, not to
/// maximize completion.
/// </summary>
public enum SessionOutcome
{
    Completed,
    PartiallyCompleted,
    Blocked,
    Replanned,
    Superseded,
    Cancelled,
    Interrupted,
    ResearchCompleted,
    DecisionReached,
}

/// <summary>
/// The structured reflection captured when a session ends (DOMAIN_MODEL.md
/// "Wrap-Up"). The outcome is required (ADR-0009); the free-text fields are
/// optional and normalized (trimmed, length-capped).
/// </summary>
public sealed record WrapUp
{
    public const int MaxFieldLength = 4000;

    public required SessionOutcome Outcome { get; init; }
    public string CompletedWork { get; init; } = "";
    public string UnfinishedWork { get; init; } = "";
    public string Blockers { get; init; } = "";
    public string FutureSelfNotes { get; init; } = "";
    public string NextAction { get; init; } = "";

    /// <summary>Trims and length-checks one wrap-up field.</summary>
    /// <exception cref="ValidationException">Over-length field.</exception>
    public static string NormalizeField(string? value, string fieldName)
    {
        var trimmed = (value ?? "").Trim();
        if (trimmed.Length > MaxFieldLength)
        {
            throw new ValidationException(
                $"The wrap-up '{fieldName}' field is limited to {MaxFieldLength} characters " +
                $"(got {trimmed.Length}).");
        }
        return trimmed;
    }
}

/// <summary>
/// A bounded period of focused work on one project (DOMAIN_MODEL.md,
/// WORK_SESSION_MODEL.md). Open until <see cref="EndedUtc"/> is set.
/// </summary>
public sealed record WorkSession
{
    public const int MaxObjectiveLength = 1000;

    /// <summary>Upper bound on a planned focus duration (ADR-0012).</summary>
    public static readonly TimeSpan MaxPlannedDuration = TimeSpan.FromHours(24);

    public required Guid Id { get; init; }
    public required Guid ProjectId { get; init; }
    public string Objective { get; init; } = "";
    public required DateTimeOffset StartedUtc { get; init; }
    public DateTimeOffset? EndedUtc { get; init; }
    public WrapUp? WrapUp { get; init; }

    /// <summary>
    /// Optional planned focus duration (ADR-0012). Null = untimed session.
    /// Additive since schema 0.1.0 (ADR-0009).
    /// </summary>
    public TimeSpan? PlannedDuration { get; init; }

    /// <summary>True while the session has not been ended. Derived, not persisted.</summary>
    [JsonIgnore]
    public bool IsOpen => EndedUtc is null;

    /// <summary>
    /// Elapsed time for a closed session (never negative — clamped to guard
    /// against clock skew), or null while the session is still open. Derived,
    /// not persisted.
    /// </summary>
    [JsonIgnore]
    public TimeSpan? Duration =>
        EndedUtc is DateTimeOffset ended
            ? (ended > StartedUtc ? ended - StartedUtc : TimeSpan.Zero)
            : null;

    /// <summary>
    /// When the focus timer is due, or null for an untimed session. Derived.
    /// </summary>
    [JsonIgnore]
    public DateTimeOffset? Deadline =>
        PlannedDuration is TimeSpan planned ? StartedUtc + planned : null;

    /// <summary>
    /// Time left on the focus timer at <paramref name="now"/> (may be negative
    /// once elapsed), or null when the session is untimed or already ended.
    /// </summary>
    public TimeSpan? RemainingAt(DateTimeOffset now) =>
        IsOpen && Deadline is DateTimeOffset deadline ? deadline - now : null;

    /// <summary>
    /// True when an open, timed session has reached or passed its deadline at
    /// <paramref name="now"/>.
    /// </summary>
    public bool IsElapsedAt(DateTimeOffset now) =>
        RemainingAt(now) is TimeSpan remaining && remaining <= TimeSpan.Zero;

    /// <summary>Trims and length-checks a session objective.</summary>
    /// <exception cref="ValidationException">Over-length objective.</exception>
    public static string NormalizeObjective(string? objective)
    {
        var trimmed = (objective ?? "").Trim();
        if (trimmed.Length > MaxObjectiveLength)
        {
            throw new ValidationException(
                $"A session objective is limited to {MaxObjectiveLength} characters " +
                $"(got {trimmed.Length}).");
        }
        return trimmed;
    }

    /// <summary>Validates an optional planned focus duration (ADR-0012).</summary>
    /// <exception cref="ValidationException">Non-positive or over the 24h cap.</exception>
    public static TimeSpan? NormalizePlannedDuration(TimeSpan? planned)
    {
        if (planned is not TimeSpan value)
        {
            return null;
        }
        if (value <= TimeSpan.Zero)
        {
            throw new ValidationException("A planned session duration must be greater than zero.");
        }
        if (value > MaxPlannedDuration)
        {
            throw new ValidationException(
                $"A planned session duration cannot exceed {MaxPlannedDuration.TotalHours:0} hours.");
        }
        return value;
    }
}
