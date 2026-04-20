from src.models import GpuType

_L40S_THRESHOLD_B = 26


def select_gpu(model_size_b: int) -> GpuType:
    if model_size_b < _L40S_THRESHOLD_B:
        return GpuType.L40S
    return GpuType.H100
