"""
Artifact fingerprinting for the ECF control plane.

Read-only SHA-256 fingerprinting of runtime artifacts. Standard library only.

Exports are resolved lazily so that running the module directly
(`python -m tools.artifact_fingerprint.fingerprint`) does not import the
submodule twice.
"""

__all__ = ["sha256_file", "sha256_bytes", "FingerprintError"]


def __getattr__(name):
    if name in __all__:
        from . import fingerprint
        return getattr(fingerprint, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
