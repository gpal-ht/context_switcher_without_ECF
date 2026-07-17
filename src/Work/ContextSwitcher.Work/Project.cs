namespace ContextSwitcher.Work;

/// <summary>Project lifecycle status. Values start minimal per ADR-0008.</summary>
public enum ProjectStatus
{
    Active,
    Archived,
}

/// <summary>
/// A meaningful body of work (DOMAIN_MODEL.md). Carries exactly the required
/// data named by docs/features/project_context_switch.md: id, name,
/// description, status, created date, updated date.
/// </summary>
public sealed record Project
{
    public const int MaxNameLength = 200;
    public const int MaxDescriptionLength = 2000;

    public required Guid Id { get; init; }
    public required string Name { get; init; }
    public string Description { get; init; } = "";
    public ProjectStatus Status { get; init; } = ProjectStatus.Active;
    public required DateTimeOffset CreatedUtc { get; init; }
    public required DateTimeOffset UpdatedUtc { get; init; }

    /// <summary>Validates and normalizes a project name.</summary>
    /// <exception cref="ValidationException">Blank or over-length name.</exception>
    public static string NormalizeName(string? name)
    {
        var trimmed = (name ?? "").Trim();
        if (trimmed.Length == 0)
        {
            throw new ValidationException("A project name is required.");
        }
        if (trimmed.Length > MaxNameLength)
        {
            throw new ValidationException(
                $"Project names are limited to {MaxNameLength} characters (got {trimmed.Length}).");
        }
        return trimmed;
    }

    /// <summary>Validates and normalizes a project description.</summary>
    /// <exception cref="ValidationException">Over-length description.</exception>
    public static string NormalizeDescription(string? description)
    {
        var trimmed = (description ?? "").Trim();
        if (trimmed.Length > MaxDescriptionLength)
        {
            throw new ValidationException(
                $"Project descriptions are limited to {MaxDescriptionLength} characters (got {trimmed.Length}).");
        }
        return trimmed;
    }
}
