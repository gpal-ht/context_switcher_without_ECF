using System.Text.Json.Serialization;

namespace ContextSwitcher.Work;

/// <summary>
/// The kind of knowledge captured against a project (ADR-0024): a free-form
/// observation, or a decision (a choice that may carry a rationale).
/// </summary>
public enum KnowledgeKind
{
    Note,
    Decision,
}

/// <summary>
/// A durable piece of project knowledge (ADR-0024): a Note or a Decision.
/// Immutable and append-only — knowledge is a record of what happened and why,
/// not editable state. A single record type (discriminated by
/// <see cref="Kind"/>) keeps the model and JSON round-trip simple; the optional
/// <see cref="Rationale"/> is only meaningful for a Decision and stays empty
/// for a Note. Persisted as one additive collection on
/// <see cref="WorkspaceState"/> (backward-compatible per ADR-0009).
/// </summary>
public sealed record KnowledgeEntry
{
    public const int MaxTextLength = 4000;
    public const int MaxRationaleLength = 4000;

    public required Guid Id { get; init; }
    public required Guid ProjectId { get; init; }
    public required KnowledgeKind Kind { get; init; }
    public required string Text { get; init; }

    /// <summary>Optional reasoning behind a Decision; always empty for a Note.</summary>
    public string Rationale { get; init; } = "";

    public required DateTimeOffset CreatedUtc { get; init; }

    /// <summary>True when a Decision carries a recorded rationale. Derived.</summary>
    [JsonIgnore]
    public bool HasRationale => Rationale.Length > 0;

    /// <summary>Validates and normalizes the required knowledge text.</summary>
    /// <exception cref="ValidationException">Blank or over-length text.</exception>
    public static string NormalizeText(string? text)
    {
        var trimmed = (text ?? "").Trim();
        if (trimmed.Length == 0)
        {
            throw new ValidationException("The note/decision text is required.");
        }
        if (trimmed.Length > MaxTextLength)
        {
            throw new ValidationException(
                $"Note/decision text is limited to {MaxTextLength} characters (got {trimmed.Length}).");
        }
        return trimmed;
    }

    /// <summary>Trims and length-checks an optional decision rationale.</summary>
    /// <exception cref="ValidationException">Over-length rationale.</exception>
    public static string NormalizeRationale(string? rationale)
    {
        var trimmed = (rationale ?? "").Trim();
        if (trimmed.Length > MaxRationaleLength)
        {
            throw new ValidationException(
                $"A decision rationale is limited to {MaxRationaleLength} characters (got {trimmed.Length}).");
        }
        return trimmed;
    }
}
