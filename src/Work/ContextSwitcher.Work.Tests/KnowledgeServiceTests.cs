namespace ContextSwitcher.Work.Tests;

/// <summary>
/// Tests for capturing and surfacing project knowledge — notes and decisions
/// (ADR-0024). Deterministic: an injected clock timestamps every entry.
/// </summary>
public sealed class KnowledgeServiceTests
{
    private static readonly DateTimeOffset T0 = new(2026, 07, 18, 09, 0, 0, TimeSpan.Zero);

    private readonly InMemoryWorkspaceStore _store = new();
    private DateTimeOffset _now = T0;
    private readonly ProjectRegistry _projects;
    private readonly WorkSessionService _sessions;
    private readonly KnowledgeService _knowledge;

    public KnowledgeServiceTests()
    {
        _projects = new ProjectRegistry(_store, () => _now);
        _sessions = new WorkSessionService(_store, () => _now);
        _knowledge = new KnowledgeService(_store, () => _now);
        _projects.CreateProject("Alpha"); // becomes the active project
    }

    [Test]
    public void AddNote_captures_text_against_the_active_project()
    {
        var entry = _knowledge.AddNote(null, "  remember the caching gotcha  ");
        Check.Equal(KnowledgeKind.Note, entry.Kind, "kind is Note");
        Check.Equal("remember the caching gotcha", entry.Text, "text trimmed");
        Check.Equal("", entry.Rationale, "a note carries no rationale");
        Check.Equal(T0, entry.CreatedUtc, "timestamp comes from the injected clock");

        var listed = _knowledge.ListKnowledgeForActiveProject();
        Check.Equal(1, listed.Count, "the note is listed for the active project");
        Check.Equal(entry.Id, listed[0].Id, "same entry surfaced");
    }

    [Test]
    public void AddDecision_records_choice_with_optional_rationale()
    {
        var entry = _knowledge.AddDecision(null, "use JSON file storage", "no server dependency");
        Check.Equal(KnowledgeKind.Decision, entry.Kind, "kind is Decision");
        Check.Equal("use JSON file storage", entry.Text, "decision text preserved");
        Check.Equal("no server dependency", entry.Rationale, "rationale preserved");
        Check.That(entry.HasRationale, "HasRationale is true when rationale is present");
    }

    [Test]
    public void AddDecision_without_rationale_leaves_it_empty()
    {
        var entry = _knowledge.AddDecision(null, "ship the CLI first");
        Check.Equal("", entry.Rationale, "rationale defaults to empty");
        Check.That(!entry.HasRationale, "HasRationale is false without a rationale");
    }

    [Test]
    public void Empty_text_is_a_validation_error()
    {
        Check.Throws<ValidationException>(() => _knowledge.AddNote(null, "   "), "blank note text");
        Check.Throws<ValidationException>(() => _knowledge.AddDecision(null, ""), "blank decision text");
    }

    [Test]
    public void Unknown_project_is_a_not_found_error()
    {
        Check.Throws<NotFoundException>(
            () => _knowledge.AddNote("Ghost", "n"), "adding to a missing project");
        Check.Throws<NotFoundException>(
            () => _knowledge.ListKnowledge("Ghost"), "listing a missing project");
    }

    [Test]
    public void Listing_is_scoped_and_most_recent_first()
    {
        var beta = _projects.CreateProject("Beta");
        _projects.SwitchActiveProject("Beta"); // Alpha was the (first) active project

        // Two entries on Beta (now active), one on Alpha by name.
        _now = T0.AddMinutes(1);
        _knowledge.AddNote(null, "beta-first");
        _now = T0.AddMinutes(2);
        _knowledge.AddDecision(null, "beta-second");
        _knowledge.AddNote("Alpha", "alpha-note");

        var betaList = _knowledge.ListKnowledge(beta.Id.ToString());
        Check.Equal(2, betaList.Count, "only Beta's two entries are scoped in");
        Check.Equal("beta-second", betaList[0].Text, "most recent first");
        Check.Equal("beta-first", betaList[1].Text, "older entry second");

        var alphaList = _knowledge.ListKnowledge("Alpha");
        Check.Equal(1, alphaList.Count, "Alpha keeps only its own note");
        Check.Equal("alpha-note", alphaList[0].Text, "named-project scope works");
    }

    [Test]
    public void ListForActiveProject_requires_an_active_project()
    {
        // A fresh workspace has no active project selected.
        var empty = new KnowledgeService(new InMemoryWorkspaceStore(), () => _now);
        Check.Throws<ValidationException>(
            () => empty.ListKnowledgeForActiveProject(), "no active project to list");
        Check.Throws<ValidationException>(
            () => empty.AddNote(null, "orphan"), "no active project to capture against");
    }

    [Test]
    public void Resume_brief_folds_in_recent_knowledge()
    {
        // A closed session gives us a brief; knowledge should ride along.
        _sessions.StartSession("design");
        _now = T0.AddMinutes(10);
        _sessions.EndSession(SessionOutcome.PartiallyCompleted, nextAction: "write tests");

        _now = T0.AddMinutes(11);
        _knowledge.AddNote(null, "watch the clock injection");
        _now = T0.AddMinutes(12);
        _knowledge.AddDecision(null, "use a single record type", "simpler JSON");

        var brief = _sessions.GetResumeBriefForActiveProject()!;
        Check.Equal(2, brief.RecentKnowledge.Count, "both entries fold into the brief");
        Check.Equal("use a single record type", brief.RecentKnowledge[0].Text, "most recent first in the brief");
        Check.Equal(SessionOutcome.PartiallyCompleted, brief.Outcome, "existing brief content is unchanged");
    }
}

/// <summary>
/// Persistence tests for project knowledge (ADR-0024): round-trip through disk
/// and additive backward-compatibility with pre-knowledge files (ADR-0009).
/// </summary>
public sealed class KnowledgePersistenceTests : IDisposable
{
    private readonly string _dir = Path.Combine(
        Path.GetTempPath(), "cs-knowledge-tests-" + Guid.NewGuid().ToString("N"));

    public void Dispose()
    {
        try { Directory.Delete(_dir, recursive: true); } catch (DirectoryNotFoundException) { }
    }

    private JsonFileWorkspaceStore NewStore() => new(_dir);

    [Test]
    public void Knowledge_round_trips_through_disk()
    {
        var store = NewStore();
        var registry = new ProjectRegistry(store);
        registry.CreateProject("Alpha");
        var knowledge = new KnowledgeService(store);
        knowledge.AddNote(null, "a persisted note");
        knowledge.AddDecision(null, "a persisted decision", "because reasons");

        // Fresh store instance (fresh-process semantics) sees the entries.
        var reloaded = new KnowledgeService(NewStore());
        var entries = reloaded.ListKnowledge("Alpha");
        Check.Equal(2, entries.Count, "both entries persisted");
        var decision = entries.First(e => e.Kind == KnowledgeKind.Decision);
        Check.Equal("a persisted decision", decision.Text, "decision text persisted");
        Check.Equal("because reasons", decision.Rationale, "rationale persisted");
        Check.That(entries.Any(e => e.Kind == KnowledgeKind.Note && e.Text == "a persisted note"),
            "note persisted");
    }

    [Test]
    public void A_pre_knowledge_file_still_loads_with_no_knowledge()
    {
        // Backward compatibility (ADR-0009 / ADR-0024): a file written before the
        // `knowledge` field existed has no such key. It must load, defaulting to
        // an empty list, and stay on the current schema version.
        var store = NewStore();
        Directory.CreateDirectory(_dir);
        File.WriteAllText(store.FilePath,
            """{ "schema_version": "0.1.0", "active_project_id": null, "projects": [], "sessions": [] }""");

        var state = store.Load();
        Check.Equal(0, state.Knowledge.Count, "missing knowledge defaults to empty");
        Check.Equal("0.1.0", state.SchemaVersion, "schema version unchanged by the additive field");
    }
}
