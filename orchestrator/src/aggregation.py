import uuid

import llm_grill

from src.models import GpuType, Result, Run


def aggregate(jsonl: str, run: Run) -> Result:
    """Delegate to llm-grill and map AggregatedMetrics onto a Result row."""
    metrics = llm_grill.aggregate(jsonl)
    return Result(
        id=uuid.uuid4(),
        run_id=run.id,
        model=run.model,
        engine=run.engine.value,
        gpu_type=GpuType(run.gpu_type_required),
        scenario=metrics.scenario,
        total_requests=metrics.total_requests,
        success_count=metrics.success_count,
        error_count=metrics.error_count,
        success_rate=metrics.success_rate,
        ttft_mean_s=metrics.ttft_mean_s,
        ttft_median_s=metrics.ttft_median_s,
        ttft_p95_s=metrics.ttft_p95_s,
        tpot_mean_s=metrics.tpot_mean_s,
        e2e_mean_s=metrics.e2e_mean_s,
        e2e_p95_s=metrics.e2e_p95_s,
        tokens_per_second_mean=metrics.tokens_per_second_mean,
        total_tokens_per_second=metrics.total_tokens_per_second,
        requests_per_second=metrics.requests_per_second,
        total_duration_s=metrics.total_duration_s,
    )
