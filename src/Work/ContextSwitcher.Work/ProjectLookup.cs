namespace ContextSwitcher.Work;

/// <summary>
/// Shared project resolution over a loaded <see cref="WorkspaceState"/>
/// (ADR-0014). Used by <see cref="ProjectRegistry"/> and
/// <see cref="WorkSessionService"/> so the two cannot drift on the semantics
/// of resolving a project by name or id.
/// </summary>
internal static class ProjectLookup
{
    /// <summary>The project whose name matches case-insensitively, or null.</summary>
    public static Project? FindByName(WorkspaceState state, string name) =>
        state.Projects.FirstOrDefault(
            p => string.Equals(p.Name, name, StringComparison.OrdinalIgnoreCase));

    /// <summary>Resolves a project by exact id or case-insensitive name.</summary>
    /// <exception cref="ValidationException">The reference is blank.</exception>
    /// <exception cref="NotFoundException">No project matches.</exception>
    public static Project Resolve(WorkspaceState state, string? nameOrId)
    {
        var query = (nameOrId ?? "").Trim();
        if (query.Length == 0)
        {
            throw new ValidationException("A project name or id is required.");
        }
        if (Guid.TryParse(query, out var id))
        {
            return state.Projects.FirstOrDefault(p => p.Id == id)
                ?? throw new NotFoundException($"No project has the id '{query}'.");
        }
        return FindByName(state, query)
            ?? throw new NotFoundException($"No project is named '{query}'.");
    }
}
