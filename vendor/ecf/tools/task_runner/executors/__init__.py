"""
AI-backed and provider-specific executors for the ECF single-task runner.

Executors are disabled by default; the Claude executor requires explicit AI
opt-in. Executors return exactly one candidate output — they never write the
final runtime output, generate authoritative provenance, or update state.
"""

__all__ = [
    "ClaudeCodeExecutor", "load_intent_taxonomy", "validate_intent_result",
    "build_prompt", "ClaudeExecutorError", "SUPPORTED_TASKS",
]


def __getattr__(name):
    if name in __all__:
        from . import claude_code
        return getattr(claude_code, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
