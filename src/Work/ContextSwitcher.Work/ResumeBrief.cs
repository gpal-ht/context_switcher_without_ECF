namespace ContextSwitcher.Work;

/// <summary>
/// The information presented when returning to a project (DOMAIN_MODEL.md
/// "Resume Brief", initial form): the most recent completed session's
/// reflection. Derived from a <see cref="WorkSession"/>; no AI (MVP non-goal).
/// </summary>
public sealed record ResumeBrief
{
    public required Guid ProjectId { get; init; }
    public required Guid SessionId { get; init; }
    public required DateTimeOffset EndedUtc { get; init; }
    public required SessionOutcome Outcome { get; init; }
    public string UnfinishedWork { get; init; } = "";
    public string Blockers { get; init; } = "";
    public string FutureSelfNotes { get; init; } = "";
    public string NextAction { get; init; } = "";

    /// <summary>
    /// Recent notes and decisions captured against the project, most recent
    /// first (ADR-0024). Additive: empty when the project has no knowledge yet.
    /// </summary>
    public IReadOnlyList<KnowledgeEntry> RecentKnowledge { get; init; } = Array.Empty<KnowledgeEntry>();

    internal static ResumeBrief FromSession(
        WorkSession session, IReadOnlyList<KnowledgeEntry>? recentKnowledge = null)
    {
        var wrapUp = session.WrapUp
            ?? throw new InvalidOperationException("A resume brief requires an ended session with a wrap-up.");
        return new ResumeBrief
        {
            ProjectId = session.ProjectId,
            SessionId = session.Id,
            EndedUtc = session.EndedUtc!.Value,
            Outcome = wrapUp.Outcome,
            UnfinishedWork = wrapUp.UnfinishedWork,
            Blockers = wrapUp.Blockers,
            FutureSelfNotes = wrapUp.FutureSelfNotes,
            NextAction = wrapUp.NextAction,
            RecentKnowledge = recentKnowledge ?? Array.Empty<KnowledgeEntry>(),
        };
    }
}
