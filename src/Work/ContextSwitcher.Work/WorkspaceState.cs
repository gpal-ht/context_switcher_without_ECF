namespace ContextSwitcher.Work;

/// <summary>
/// The persisted state of the (single-user) workspace: the project list and
/// the active-project selection. This is the unit the store port loads and
/// saves; invariants are enforced by <see cref="ProjectRegistry"/>.
/// </summary>
public sealed class WorkspaceState
{
    /// <summary>Persistence schema version (ADR-0008). Bump deliberately.</summary>
    public const string CurrentSchemaVersion = "0.1.0";

    public string SchemaVersion { get; set; } = CurrentSchemaVersion;
    public Guid? ActiveProjectId { get; set; }
    public List<Project> Projects { get; set; } = new();
}
