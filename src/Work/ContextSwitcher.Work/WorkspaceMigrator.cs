namespace ContextSwitcher.Work;

/// <summary>
/// Explicit schema-version handling for <see cref="WorkspaceState"/> (ADR-0026).
///
/// The on-disk file carries a semantic <c>schema_version</c>. On load the
/// migrator compares it to <see cref="WorkspaceState.CurrentSchemaVersion"/>:
///
///   * equal  -&gt; loaded as-is;
///   * older  -&gt; upgraded by the ordered <see cref="Migrations"/> pipeline
///               (empty today; 0.1.0 is the first schema) and re-stamped to the
///               current version in memory. The upgrade is persisted on the next
///               save; loading never rewrites the file on its own;
///   * blank  -&gt; treated as the oldest possible version and upgraded as above;
///   * newer  -&gt; rejected with a <see cref="StoreCorruptException"/> so a build
///               never silently discards fields it does not understand.
///
/// Future breaking shape changes bump CurrentSchemaVersion and append a step to
/// <see cref="Migrations"/> (ascending order); each step upgrades state produced
/// by the prior version to the next, keeping older files loadable.
/// </summary>
internal static class WorkspaceMigrator
{
    /// <summary>A single forward migration step.</summary>
    /// <param name="From">Lower bound (inclusive) of versions this step upgrades.</param>
    /// <param name="To">The version this step produces.</param>
    /// <param name="Apply">Upgrades the state to the <paramref name="To"/> shape.</param>
    internal sealed record Migration(
        Version From, Version To, Func<WorkspaceState, WorkspaceState> Apply);

    /// <summary>
    /// Ordered upgrade pipeline. Empty today: 0.1.0 is the first and only schema,
    /// so an older or blank version needs no shape change, only a re-stamp. New
    /// entries append here in ascending <see cref="Migration.To"/> order.
    /// </summary>
    internal static readonly IReadOnlyList<Migration> Migrations = new List<Migration>();

    internal static readonly Version Current =
        ParseOrThrow(WorkspaceState.CurrentSchemaVersion, WorkspaceState.CurrentSchemaVersion, isFileValue: false);

    /// <summary>
    /// Returns the state at the current schema, upgrading it if needed. May
    /// mutate and returns the same instance for the common (equal-version) path.
    /// </summary>
    /// <exception cref="StoreCorruptException">
    /// The file's version is newer than this build supports, or unparseable.
    /// </exception>
    public static WorkspaceState Migrate(WorkspaceState state, string filePath)
    {
        var found = ParseFileVersion(state.SchemaVersion, filePath);

        if (found > Current)
        {
            throw new StoreCorruptException(
                $"The workspace file at {filePath} uses schema version " +
                $"'{state.SchemaVersion}', but this build supports " +
                $"'{WorkspaceState.CurrentSchemaVersion}'. Your data has not been " +
                "modified; use a matching application version.");
        }

        if (found == Current)
        {
            return state;
        }

        // found < Current: apply each applicable step in order, then re-stamp.
        var version = found;
        foreach (var step in Migrations)
        {
            if (version >= step.From && version < step.To)
            {
                state = step.Apply(state);
                version = step.To;
            }
        }
        state.SchemaVersion = WorkspaceState.CurrentSchemaVersion;
        return state;
    }

    private static Version ParseFileVersion(string? raw, string filePath)
    {
        // Blank/absent version == a pre-versioned file == the oldest schema.
        if (string.IsNullOrWhiteSpace(raw))
        {
            return new Version(0, 0, 0);
        }
        return ParseOrThrow(raw, filePath, isFileValue: true);
    }

    private static Version ParseOrThrow(string raw, string filePath, bool isFileValue)
    {
        if (Version.TryParse(raw.Trim(), out var v))
        {
            // Normalize "x.y" to "x.y.0" so comparisons are total and stable.
            return new Version(v.Major, Math.Max(v.Minor, 0), Math.Max(v.Build, 0));
        }
        if (!isFileValue)
        {
            throw new InvalidOperationException(
                $"CurrentSchemaVersion '{raw}' is not a valid version.");
        }
        throw new StoreCorruptException(
            $"The workspace file at {filePath} has an unparseable schema version " +
            $"'{raw}'. Your data has not been modified; repair or move the file and retry.");
    }
}
