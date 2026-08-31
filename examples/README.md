# AEGIS-X Integration Examples

This directory contains integration guides and workflow examples for connecting models and datasets to AEGIS-X.

## Example Workflow

1. Train or export your scikit-learn model to `.joblib` or `.pkl` format:
   ```python
   import joblib
   from sklearn.ensemble import RandomForestClassifier
   
   clf = RandomForestClassifier()
   clf.fit(X_train, y_train)
   joblib.dump(clf, "my_model.joblib")
   ```

2. Export baseline reference and current evaluation datasets to CSV:
   ```python
   X_train.to_csv("reference.csv", index=False)
   X_eval.to_csv("evaluation.csv", index=False)
   ```

3. Initialize AEGIS-X Integration Engine:
   ```python
   from aegis.core import SklearnModelAdapter, CSVDataLoader, IntegrationValidator
   
   adapter = SklearnModelAdapter.load("my_model.joblib")
   ref_ds = CSVDataLoader.load("reference.csv")
   eval_ds = CSVDataLoader.load("evaluation.csv")
   
   report = IntegrationValidator.validate(
       model_adapter=adapter,
       reference_dataset=ref_ds,
       evaluation_dataset=eval_ds
   )
   ```
