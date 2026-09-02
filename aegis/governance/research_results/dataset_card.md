# AEGIS-X Module 14 Canonical Evidence Dataset Card

**Dataset Version**: 1.0.0  
**Builder Config Hash**: `8e7fd68470057c99`  
**Domains Included**: ['synthetic_degradation_trajectory', 'classification_breast_cancer', 'digits_parity']  
**Horizons**: K = [1, 2, 3, 5] controlled_degradation_states  

## Overview
This canonical evidence dataset combines reliability signals, detector diagnostics, and forward-looking ground-truth targets across synthetic degradation trajectories and tabular cross-domain validation fixtures.

## Domain Breakdown
- **synthetic_degradation_trajectory**: 240 rows
- **classification_breast_cancer**: 2276 rows
- **digits_parity**: 7188 rows

## Split Protocol
Group-aware 60/20/20 partitioning by trajectory ID with 100% zero-overlap verification.
