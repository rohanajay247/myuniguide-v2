"""Langfuse tracing.

Optional by design, twice over: if keys are absent the decorators become
no-ops, and if the package itself is missing they do too. The slim serving
image omits langfuse, and tracing should never be the reason the app fails
to start.

The keys are pushed into os.environ because Langfuse's @observe decorator
constructs its own client from environment variables — it never sees values
that pydantic-settings loaded into a Settings object.
"""

import os
from functools import lru_cache

from myuniguide.config import settings

if settings.tracing_enabled:
    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
    os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)


@lru_cache(maxsize=1)
def _client():
    if not settings.tracing_enabled:
        return None
    try:
        from langfuse import get_client
    except ImportError:
        return None
    return get_client()


def observe(name: str):
    """Decorator that traces a function as a span, or does nothing."""

    def decorator(fn):
        if not settings.tracing_enabled:
            return fn
        try:
            from langfuse import observe as lf_observe
        except ImportError:
            return fn
        return lf_observe(name=name)(fn)

    return decorator


def update_generation(model: str, usage) -> None:
    """Attach token usage to the current span so Langfuse can compute cost."""
    client = _client()
    if not client or usage is None:
        return
    try:
        client.update_current_generation(
            model=model,
            usage_details={
                "input": usage.prompt_token_count or 0,
                "output": usage.candidates_token_count or 0,
            },
        )
    except Exception:  # noqa: BLE001
        pass


def flush() -> None:
    """Langfuse batches in the background; call before the process exits."""
    client = _client()
    if client:
        client.flush()