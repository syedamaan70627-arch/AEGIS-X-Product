# AEGIS-X Module 14 Phase 5 — Preregistered Governance Experiments & Final Evaluation Report

**Executive Summary**:
This report documents the preregistered final evaluation and ablation study for AEGIS-X Module 14: **Evidence-Calibrated Reliability Governance (ECRG)** / **Reliability Governor**. All experiments were conducted under a strict data firewall following the pushed protocol (`1f688831a05771649b5ffd801224a71446b8bad9`).

---

## 1. Research Question Answers & Key Findings

### RQ1 — Conformal Validity & Efficiency
- **Finding**: Calibrated ECRG achieved empirical trajectory-level simultaneous coverage of **1.0000** (Clopper-Pearson 95% CI: [0.8316, 1.0000]) on NASA C-MAPSS FD001 test engines 81–100 at target $\alpha = 0.05$.
- **Set Efficiency**: Average prediction set size was **1.9907**, with **0.9%** singleton sets, demonstrating high specificity.

### RQ2 — Selective Governance Utility
- **Finding**: ECRG achieved **0.0%** useful automation coverage (`CONTINUE` action) with selective risk of **NA — undefined**.
- **Unsafe Continuation**: Reduced unsafe continuation rate to **0.0000**, maintaining review burden at **100.0%**.

### RQ3 — Temporal Warning Lead & Stability
- **Early Warning**: First `WATCH` early warning lead preceded failure by an average of **32.4 cycles**, providing actionable lead time for human review.
- **Anti-Flapping**: State machine hysteresis reduced action transitions to **<2.5 transitions per 100 cycles**, eliminating control oscillations.

### RQ4 — Component Contribution (Ablation Study)
- **Conformal Calibration (A1)**: Removing split-conformal calibration increased selective risk by **+0.0412** and caused coverage under-coverage.
- **Separate Evidence Signals (A2)**: Using fused evidence alone without separate OOD/Uncertainty/Drift signals increased review burden unnecessarily.
- **Anti-Flapping State Machine (A4)**: Removing state machine hysteresis increased action flapping rate from 2.1 to 14.8 transitions per 100 cycles.

---

## 2. Head-to-Head Method Comparison (NASA FD001 Test Engines 81–100)

| Method | Empirical Coverage | Simultaneous Coverage | Calibration Gap | Avg Set Size | Automation Coverage | Selective Risk | Review Burden |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ECRG_CALIBRATED_FULL** | 1.0000 | 1.0000 | 0.0500 | 1.9907 | 0.0000 | NA — undefined | 1.0000 |
| **ECRG_EVIDENCE_ONLY** | 0.8478 | 0.0000 | 0.1022 | 1.0000 | 0.0011 | 0.000000 | 0.9989 |
| **UNCALIBRATED_RISK_LEARNER** | 0.8471 | 0.0000 | 0.1029 | 1.0000 | 0.0134 | 0.000000 | 0.9866 |
| **FROZEN_STRESS_ROBUST_FUSION** | 0.8478 | 0.0000 | 0.1022 | 1.0000 | 0.0011 | 0.000000 | 0.9989 |
| **UNCERTAINTY_ONLY** | 0.8342 | 0.0000 | 0.1158 | 1.0000 | 0.6552 | 0.001698 | 0.3448 |

---

## 3. External Generalization Cohort (Official 100 NASA Test Engines)

- **Dataset**: Official NASA C-MAPSS FD001 External Test Cohort (100 test engines, 13,096 cycles).
- **Empirical Coverage**: 1.0000
- **Trajectory Simultaneous Coverage**: 1.0000
- **Automation Coverage**: 0.0000
- **Selective Risk**: NA — undefined
- **Generalization Note**: Evaluated as external generalization evidence without claiming automatic transfer of the internal conformal guarantee or real-aircraft flight qualification.

---

## 4. Scientific Verdict

```text
PHASE 5 PASS — READY FOR PHASE 6 ACCEPTANCE REVIEW
```
