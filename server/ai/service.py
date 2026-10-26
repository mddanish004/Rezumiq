"""AI run history, ported from modules/ai-runs/ai-runs.service.ts."""

from __future__ import annotations

from django.db.models import Q, Sum

from ai.models import AiRun
from ai.pricing import known_cost_usd_micros
from usage.quotas import period_start


def list_ai_runs(user_id) -> dict:
    """Only usage numbers: never prompts, outputs, errors or resume content."""
    since = period_start()
    runs = list(
        AiRun.objects.filter(user_id=user_id)
        .order_by("-created_at")
        .values(
            "id",
            "created_at",
            "step",
            "status",
            "model",
            "byok",
            "input_tokens",
            "output_tokens",
            "cost_usd_micros",
            "latency_ms",
            "resume_id",
        )[:20]
    )
    month = AiRun.objects.filter(user_id=user_id, created_at__gte=since).aggregate(
        cost=Sum("cost_usd_micros", default=0)
    )
    unpriced = AiRun.objects.filter(
        Q(input_tokens__gt=0) | Q(output_tokens__gt=0),
        user_id=user_id,
        created_at__gte=since,
        cost_usd_micros=0,
    ).count()
    return {
        "periodStart": since,
        "monthCostUsdMicros": month["cost"],
        "monthUnpricedRuns": unpriced,
        "runs": [
            {
                **run,
                "costUsdMicros": known_cost_usd_micros(
                    run["cost_usd_micros"], run["input_tokens"], run["output_tokens"]
                ),
            }
            for run in runs
        ],
    }
