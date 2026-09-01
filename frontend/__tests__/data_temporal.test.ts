/**
 * AEGIS-X Temporal Trajectory Dataset UI & Filtering Tests
 */

import test from "node:test";
import assert from "node:assert/strict";
import { DatasetRecord } from "../types/api";

const mockDatasets: DatasetRecord[] = [
  {
    dataset_id: "ds-ref-1",
    model_id: "mod-1",
    dataset_type: "REFERENCE",
    filename: "reference_dataset.csv",
    num_samples: 398,
    num_features: 30,
    feature_names: ["f1", "f2"],
    has_target: true,
    created_at: "2026-09-01T00:00:00Z",
    status: "registered",
  },
  {
    dataset_id: "ds-eval-1",
    model_id: "mod-1",
    dataset_type: "EVALUATION",
    filename: "evaluation_dataset.csv",
    num_samples: 171,
    num_features: 30,
    feature_names: ["f1", "f2"],
    has_target: true,
    created_at: "2026-09-01T00:00:00Z",
    status: "registered",
  },
  {
    dataset_id: "ds-traj-1",
    model_id: "mod-1",
    dataset_type: "TEMPORAL_TRAJECTORY",
    filename: "sample_temporal_trajectory.csv",
    target_column: "Failure_Onset_Next",
    num_samples: 60,
    num_features: 4,
    feature_names: ["ood_risk", "uncertainty_risk", "drift_risk", "fused_risk"],
    has_target: true,
    created_at: "2026-09-01T00:00:00Z",
    status: "registered",
  },
];

test("Data Category Filtering: Reference Datasets Filter", () => {
  const referenceDatasets = mockDatasets.filter((d) => d.dataset_type === "REFERENCE");
  assert.equal(referenceDatasets.length, 1);
  assert.equal(referenceDatasets[0].dataset_id, "ds-ref-1");
  assert.equal(referenceDatasets.some((d) => (d.dataset_type as string) === "TEMPORAL_TRAJECTORY"), false);
});

test("Data Category Filtering: Evaluation Datasets Filter", () => {
  const evaluationDatasets = mockDatasets.filter((d) => d.dataset_type === "EVALUATION");
  assert.equal(evaluationDatasets.length, 1);
  assert.equal(evaluationDatasets[0].dataset_id, "ds-eval-1");
  assert.equal(evaluationDatasets.some((d) => (d.dataset_type as string) === "TEMPORAL_TRAJECTORY"), false);
});

test("Data Category Filtering: Temporal Trajectory Datasets Filter", () => {
  const temporalDatasets = mockDatasets.filter(
    (d) => d.dataset_type === "TEMPORAL_TRAJECTORY" || d.dataset_type === "PREDICTION_TRAJECTORY"
  );
  assert.equal(temporalDatasets.length, 1);
  assert.equal(temporalDatasets[0].dataset_id, "ds-traj-1");
  assert.equal(temporalDatasets.some((d) => d.dataset_type === "REFERENCE"), false);
  assert.equal(temporalDatasets.some((d) => d.dataset_type === "EVALUATION"), false);
});

test("Prediction & Warning Setup Selector Filtering", () => {
  const trajectoryDatasets = mockDatasets.filter(
    (d) => d.dataset_type === "TEMPORAL_TRAJECTORY" || d.dataset_type === "PREDICTION_TRAJECTORY"
  );
  assert.equal(trajectoryDatasets.length, 1);
  assert.equal(trajectoryDatasets[0].filename, "sample_temporal_trajectory.csv");
});
