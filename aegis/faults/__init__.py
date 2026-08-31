"""
AEGIS-X Fault Injection and Failure Discovery Module.
"""

from aegis.faults.failure_discovery import FailureDiscoveryEngine
from aegis.faults.transformations import (
    FaultInjector,
    inject_channel_swap,
    inject_feature_bias,
    inject_gain_error,
    inject_sign_inversion,
    inject_stuck_at,
)

__all__ = [
    "FaultInjector",
    "FailureDiscoveryEngine",
    "inject_feature_bias",
    "inject_gain_error",
    "inject_stuck_at",
    "inject_channel_swap",
    "inject_sign_inversion",
]
