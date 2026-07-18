namespace ContextSwitcher.Work;

/// <summary>
/// The persisted state of the (single-user) workspace: the project list, the
/// active-project selection, and the work-session history. This is the unit
/// the store port loads and saves; invariants are enforced by
/// <see cref="ProjectRegistry"/> and <see cref="WorkSessionService"/>.
/// </summary>
public sealed class WorkspaceState
{
    /// <summary>
    /// Persistence schema version. Bump only for BREAKING shape changes;
    /// additive optional fields stay on the current version (ADR-0009).
    /// </summary>
    public const string CurrentSchemaVersion = "0.1.0";

    public string SchemaVersion { get; set; } = CurrentSchemaVersion;
    public Guid? ActiveProjectId { get; set; }
    public List<Project> Projects { get; set; } = new();

    /// <summary>
    /// Work-session history (ADR-0009). Additive since 0.1.0: a file written
    /// before sessions existed simply has none.
    /// </summary>
    public List<WorkSession> Sessions { get; set; } = new();

    /// <summary>
    /// Project knowledge: notes and decisions (ADR-0024). Additive since 0.1.0:
    /// a file written before knowledge capture existed simply has none, and
    /// deserializes to an empty list.
    /// </summary>
    public List<KnowledgeEntry> Knowledge { get; set; } = new();
}
