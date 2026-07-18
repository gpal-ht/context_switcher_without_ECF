using System.Text.Json.Serialization;

namespace ContextSwitcher.Work;

/// <summary>
/// Completion state of a <see cref="NextAction"/> (ADR-0025). Values start
/// minimal, mirroring <see cref="ProjectStatus"/>.
/// </summary>
public enum NextActionStatus
{
    Open,
    Done,
}

/// <summary>
/// A lightweight, per-project "next-action" — an open work item that makes
/// "what remains unfinished" explicit and is surfaced on resume (ADR-0025).
/// Immutable; completion is recorded by producing a new value with
/// <see cref="NextActionStatus.Done"/> and a <see cref="CompletedUtc"/>.
/// </summary>
public sealed record NextAction
{
    public const int MaxTextLength = 1000;

    public required Guid Id { get; init; }
    public required Guid ProjectId { get; init; }
    public required string Text { get; init; }
    public required DateTimeOffset CreatedUtc { get; init; }

    /// <summary>Completion state. Defaults to open; additive since ADR-0025.</summary>
    public NextActionStatus Status { get; init; } = NextActionStatus.Open;

    /// <summary>When the action was completed, or null while it is open.</summary>
    public DateTimeOffset? CompletedUtc { get; init; }

    /// <summary>True while the action has not been completed. Derived, not persisted.</summary>
    [JsonIgnore]
    public bool IsOpen => Status == NextActionStatus.Open;

    /// <summary>Trims and validates next-action text.</summary>
    /// <exception cref="ValidationException">Blank or over-length text.</exception>
    public static string NormalizeText(string? text)
    {
        var trimmed = (text ?? "").Trim();
        if (trimmed.Length == 0)
        {
            throw new ValidationException("A next-action needs some text.");
        }
        if (trimmed.Length > MaxTextLength)
        {
            throw new ValidationException(
                $"A next-action is limited to {MaxTextLength} characters (got {trimmed.Length}).");
        }
        return trimmed;
    }
}
