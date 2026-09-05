"""LandSight AI - Multiclass Risk Classification (XGBoost).

Trains an XGBoost multiclass classifier to predict project land acquisition risk category
(Low, Medium, High, Critical) with 80/20 split, 5-fold Stratified Cross-Validation, and
hyperparameter tuning.
"""

import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
import xgboost as xgb

from typing import Optional

# Project paths
ml_dir = Path(__file__).resolve().parent
root_dir = ml_dir.parent
sys.path.insert(0, str(root_dir))

from ml.features import (
    ALL_FEATURE_COLUMNS,
    INV_RISK_CATEGORY_MAP,
    RISK_CATEGORY_MAP,
    load_feature_dataset,
)


def train_risk_classifier(output_path: Optional[Path] = None):
    """Trains, tunes, and evaluates XGBoost risk classifier."""
    print("=" * 60)
    print("LandSight AI - Training Multiclass Risk Classifier (XGBoost)")
    print("=" * 60)

    # 1. Load engineered features directly from PostgreSQL
    print("[*] Pulling relational project records & features from PostgreSQL...")
    X, y, df, encoders = load_feature_dataset()
    print(f"[+] Loaded {len(X)} projects with {len(ALL_FEATURE_COLUMNS)} features.")

    # Check class distribution
    class_counts = pd.Series(y).map(INV_RISK_CATEGORY_MAP).value_counts()
    print("[*] Target Class Distribution:")
    for cat, cnt in class_counts.items():
        print(f"    {cat:<10}: {cnt:>5} ({cnt / len(y) * 100:.1f}%)")

    # 2. Stratified 80/20 Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"[+] Train set: {len(X_train)} samples | Test set: {len(X_test)} samples")

    # 3. 5-Fold Stratified Cross-Validation & Hyperparameter Tuning
    print("[*] Performing 5-Fold Stratified Cross-Validation & Hyperparameter Grid Search...")
    base_clf = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=4,
        eval_metric="mlogloss",
        random_state=42,
        tree_method="hist",
    )

    param_grid = {
        "max_depth": [3, 4, 5],
        "learning_rate": [0.05, 0.1],
        "n_estimators": [100, 180],
        "subsample": [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0],
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    grid_search = GridSearchCV(
        estimator=base_clf,
        param_grid=param_grid,
        cv=cv,
        scoring="f1_weighted",
        n_jobs=-1,
        verbose=1,
    )

    grid_search.fit(X_train, y_train)
    best_clf = grid_search.best_estimator_

    print(f"\n[+] Best Hyperparameters: {grid_search.best_params_}")
    print(f"[+] Best 5-Fold CV Weighted F1: {grid_search.best_score_:.4f}")

    # 4. Evaluation on Held-out 20% Test Set
    y_pred = best_clf.predict(X_test)
    y_proba = best_clf.predict_proba(X_test)

    test_acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    target_names = [INV_RISK_CATEGORY_MAP[i] for i in range(4)]
    report = classification_report(y_test, y_pred, target_names=target_names, digits=4)
    report_dict = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)
    conf_mat = confusion_matrix(y_test, y_pred)

    print("\n" + "=" * 60)
    print("TEST SET EVALUATION RESULTS")
    print("=" * 60)
    print(f"Test Accuracy:       {test_acc * 100:.2f}%")
    print(f"Macro F1-Score:      {macro_f1:.4f}")
    print(f"Weighted F1-Score:   {weighted_f1:.4f}\n")
    print("Classification Report:")
    print(report)
    print("Confusion Matrix (Rows=True, Cols=Predicted):")
    header = "          " + "  ".join([f"{name[:8]:>8}" for name in target_names])
    print(header)
    for idx, row in enumerate(conf_mat):
        row_str = "  ".join([f"{val:>8}" for val in row])
        print(f"{target_names[idx]:<10} {row_str}")
    print("=" * 60)

    # 5. Save Model Artifact Bundle
    models_dir = ml_dir / "models"
    models_dir.mkdir(exist_ok=True, parents=True)
    model_bundle_path = models_dir / "risk_classifier.joblib"

    bundle = {
        "model": best_clf,
        "feature_names": ALL_FEATURE_COLUMNS,
        "encoders": encoders,
        "label_map": RISK_CATEGORY_MAP,
        "inv_label_map": INV_RISK_CATEGORY_MAP,
        "best_params": grid_search.best_params_,
        "cv_score": grid_search.best_score_,
        "metrics": {
            "accuracy": test_acc,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "report_dict": report_dict,
            "confusion_matrix": conf_mat.tolist(),
        },
    }

    joblib.dump(bundle, model_bundle_path)
    print(f"\n[+] Saved model artifact to: {model_bundle_path}")

    return bundle, X_test, y_test


if __name__ == "__main__":
    train_risk_classifier()
