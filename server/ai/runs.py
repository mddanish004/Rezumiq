"""AI run accounting: reserve a plan-charged run, then record its result.

Ported from lib/ai/generate.ts's reserve/record path; the HTTP call itself stays in
ai.generate so tests can mock it.
"""

from __future__ import annotations

from ai.models import AiRun
from ai.pricing import cost_usd_micros
from usage.quotas import reserve_ai_run


def reserve_run(user_id, kind, step, resume_id=None, job_id=None) -> str | None:
    """Reserves a plan-charged run before the model is called, so parallel requests can't all
    slip under the limit. Runs on the user's own key cost us nothing and are logged afterwards."""
    from ai_keys.service import has_user_ai_key

    if has_user_ai_key(user_id):
        return None
    return reserve_ai_run(user_id, kind, step, resume_id=resume_id, job_id=job_id)


def record_run(
    user_id,
    run_id=None,
    step=AiRun.Step.ATS_MATCH,
    resume_id=None,
    job_id=None,
    result=None,
    error=False,
) -> str | None:
    """Fills the run row in: updates a reserved run, or creates one for BYOK calls."""
    result = result or {}
    tokens = result.get("tokens") or {}
    values = {
        "model": f"{result.get('provider', '')}:{result.get('model', 'pending')}",
        "error": "model request failed" if error else None,
        "status": AiRun.Status.FAILED if error else AiRun.Status.SUCCEEDED,
        "input_tokens": tokens.get("input", 0) or 0,
        "cached_input_tokens": tokens.get("cached", 0) or 0,
        "output_tokens": tokens.get("output", 0) or 0,
        "cost_usd_micros": cost_usd_micros(result.get("model", ""), tokens),
    }
    try:
        if run_id:
            AiRun.objects.filter(id=run_id).update(**values)
            return run_id
        run = AiRun.objects.create(
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            step=step,
            byok=True,
            **values,
        )
        return str(run.id)
    except Exception:  # noqa: BLE001
        return run_id
