"""
AEGIS-X Paired Fusion Comparison Module (Module 13).

Provides paired metric difference calculations for testing the central fusion hypothesis.
"""

from typing import Tuple


def calculate_paired_gain(
    fusion_aupr: float,
    best_individual_aupr: float,
) -> Tuple[float, bool]:
    """
    Computes signed paired gain: fusion_aupr - best_individual_aupr
    Returns: (paired_gain, is_fusion_win)
    """
    gain = float(fusion_aupr - best_individual_aupr)
    is_win = bool(fusion_aupr >= best_individual_aupr)
    return gain, is_win
