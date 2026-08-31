"""
Unit tests for AEGIS-X Paired Fusion Comparison Module (Module 13).
"""

import pytest

from aegis.evaluation.paired_comparison import calculate_paired_gain


def test_calculate_paired_gain_positive():
    gain, is_win = calculate_paired_gain(fusion_aupr=0.85, best_individual_aupr=0.80)

    assert pytest.approx(gain, 1e-5) == 0.05
    assert is_win is True


def test_calculate_paired_gain_negative():
    gain, is_win = calculate_paired_gain(fusion_aupr=0.80, best_individual_aupr=0.85)

    assert pytest.approx(gain, 1e-5) == -0.05
    assert is_win is False
