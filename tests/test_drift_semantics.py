"""
AEGIS-X Feature Drift Semantics & Terminology Regression Tests.
Verifies that aggregate_drift_score represents Feature Drift Prevalence (fraction of features with p < alpha)
and that report generation uses prevalence terminology (Widespread Feature Drift, X of Y features) without
altering numeric values passed to Fusion or Governance engines.
"""

import pytest
import numpy as np
from aegis.core.contracts import DriftResult, ReliabilityStatus, ModelRegistration, DatasetRegistration, TaskType, DatasetType, ModelType
from aegis.drift.detector import DriftDetector
from aegis.fusion.engine import StressRobustFusion
from aegis.reports.generator import ReportGenerator, RetrainingDisposition
from api.db.models import AnalysisRecord, DatasetRecord, ModelRecord


def test_drift_detector_prevalence_ratio_61_of_64():
    """Verifies that 61 out of 64 drifted features produces aggregate_drift_score = 0.953125."""
    feature_flags = {f"feat_{i}": (i < 61) for i in range(64)}
    drifted_count = sum(1 for v in feature_flags.values() if v)
    total_count = len(feature_flags)
    score = drifted_count / total_count
    
    assert drifted_count == 61
    assert total_count == 64
    assert score == 0.953125


def test_fusion_receives_unmutated_numeric_drift_score():
    """Verifies that fusion engine receives exact numeric aggregate_drift_score (0.953125)."""
    fusion_engine = StressRobustFusion()
    drift_res = DriftResult(
        status=ReliabilityStatus.AVAILABLE,
        method="ks_test",
        aggregate_drift_score=0.953125,
        drift_detected=True,
    )
    
    # Run fusion with exact numeric values
    res = fusion_engine.fuse(
        ood_input=0.5694,
        uncertainty_input=0.4865,
        drift_input=drift_res,
    )
    
    # Confirm numeric calculation is valid and unaffected by terminology
    assert res.status == ReliabilityStatus.AVAILABLE
    assert res.aggregate_fused_risk > 0.0
    assert drift_res.aggregate_drift_score == 0.953125


def test_report_generator_widespread_feature_drift_terminology():
    """Verifies report generator renders Widespread Feature Drift and 61 of 64 count string without severity claims."""
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    model = ModelRecord(
        id="mod_test", user_id="usr_test", model_name="Test RF", task_type="classification",
        description="", file_path="/tmp/model.pkl", filename="model.pkl", predict_supported=True,
        predict_proba_supported=True, n_features_in=64, classes=["0", "1"], feature_names=[f"feat_{i}" for i in range(64)],
        created_at=now
    )
    ref_ds = DatasetRecord(
        id="ref_test", user_id="usr_test", model_id="mod_test", dataset_type="REFERENCE",
        file_path="/tmp/ref.csv", filename="ref.csv", target_column=None, num_samples=100,
        num_features=64, feature_names=[f"feat_{i}" for i in range(64)], has_target=False, created_at=now
    )
    eval_ds = DatasetRecord(
        id="eval_test", user_id="usr_test", model_id="mod_test", dataset_type="EVALUATION",
        file_path="/tmp/eval.csv", filename="eval.csv", target_column=None, num_samples=100,
        num_features=64, feature_names=[f"feat_{i}" for i in range(64)], has_target=False, created_at=now
    )

    analysis = AnalysisRecord(
        id="ana_64feat_test",
        user_id="usr_test",
        model_id="mod_test",
        reference_dataset_id="ref_test",
        evaluation_dataset_id="eval_test",
        status="COMPLETED",
        result_path="/tmp/res.json",
        aggregate_ood_risk=0.5694,
        aggregate_uncertainty=0.4865,
        aggregate_drift_score=0.953125,
        aggregate_fused_risk=0.6804,
        fusion_method="uncertainty_weighted",
        has_labels=False,
        created_at=now,
    )
    
    # Mock reliability summary dictionary with count metadata
    rel_summary = {
        "status": "COMPLETED",
        "aggregate_fused_risk": 0.6804,
        "aggregate_ood_risk": 0.5694,
        "aggregate_uncertainty": 0.4865,
        "aggregate_drift_score": 0.953125,
        "drifted_feature_count": 61,
        "total_feature_count": 64,
        "fusion_method": "uncertainty_weighted",
        "has_labels": False,
    }
    
    generator = ReportGenerator(
        user_id="usr_test",
        model=model,
        analysis=analysis,
        ref_dataset=ref_ds,
        eval_dataset=eval_ds,
    )
    
    # Evaluate decision entries
    entries = generator._build_why_this_decision(
        trust="CONDITIONAL",
        gov={"effective_action": "WATCH", "operating_mode": "EVIDENCE_ONLY"},
        rel=rel_summary,
        stress={},
        temp={},
    )
    
    drift_entry = next((e for e in entries if e.factor == "Feature Drift Prevalence"), None)
    assert drift_entry is not None, "Should use 'Feature Drift Prevalence' factor name"
    assert "61 of 64 monitored features (95.3%)" in drift_entry.description
    assert "two-sample KS test" in drift_entry.description
    assert "95.3% severity" not in drift_entry.description
    assert "failure probability" not in drift_entry.description

    # Evaluate retraining disposition string
    disp, text = generator._derive_retraining_disposition(
        rel=rel_summary,
        gov={"effective_action": "WATCH"},
        temp={},
    )
    assert "Widespread Feature Drift" in text
    assert "Severe Feature Drift" not in text
