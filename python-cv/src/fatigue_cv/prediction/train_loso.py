import os
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import joblib

def train_loso(dataset_path: str = r"E:\UTA-RLDD\extracted-features\all_subjects_windows.csv",
               report_out_path: str = r"E:\UTA-RLDD\models\fatigue_loso_evaluation.txt",
               cm_out_path: str = r"E:\UTA-RLDD\models\fatigue_loso_confusion.json",
               final_model_path: str = r"E:\UTA-RLDD\models\fatigue_final.joblib"):
    
    os.makedirs(os.path.dirname(report_out_path), exist_ok=True)
    
    # 1. Load Data
    df = pd.read_csv(dataset_path)
    
    feature_cols = [
        "ear_mean", "ear_min", "mar_mean", "mar_max",
        "blink_rate_mean", "blink_rate_max", "yawn_rate_mean", "yawn_rate_max",
        "closure_duration_max", "pitch_median", "pitch_std",
        "yaw_median", "yaw_std", "roll_median", "roll_std"
    ]
    target_col = "kss_label"
    group_col = "subject_id"
    
    X = df[feature_cols]
    y = df[target_col]
    groups = df[group_col]
    
    # 2 & 3. LOSO CV Setup
    logo = LeaveOneGroupOut()
    classes = [0, 5, 10]
    
    # Storage for aggregate metrics
    y_true_all = []
    y_pred_all = []
    
    report_lines = []
    report_lines.append("=========================================")
    report_lines.append("ACADEMIC LOSO-CV EVALUATION")
    report_lines.append("=========================================")
    
    # 4. Perform Folds
    fold_idx = 1
    for train_idx, test_idx in logo.split(X, y, groups):
        X_train, y_train, g_train = X.iloc[train_idx], y.iloc[train_idx], groups.iloc[train_idx]
        X_test, y_test, g_test = X.iloc[test_idx], y.iloc[test_idx], groups.iloc[test_idx]
        
        test_subject = g_test.iloc[0]
        train_subjects = sorted(g_train.unique().tolist())
        
        pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        
        # Fit ONLY on training subjects
        pipeline.fit(X_train, y_train)
        
        # Predict ONLY on held-out subject
        y_pred = pipeline.predict(X_test)
        
        y_true_all.extend(y_test)
        y_pred_all.extend(y_pred)
        
        # Metrics for this fold
        acc = accuracy_score(y_test, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)
        
        # 6. Report Fold Metrics
        report_lines.append(f"\n--- FOLD {fold_idx} ---")
        report_lines.append(f"Test Subject:  {test_subject} ({len(X_test)} windows)")
        report_lines.append(f"Train Subjects: {train_subjects} ({len(X_train)} windows)")
        report_lines.append(f"Accuracy:       {acc:.4f}")
        report_lines.append(f"Macro P/R/F1:   {prec:.4f} / {rec:.4f} / {f1:.4f}")
        
        fold_idx += 1
        
    # 5. Aggregate Metrics
    report_lines.append("\n=========================================")
    report_lines.append("OVERALL AGGREGATE METRICS (All Folds)")
    report_lines.append("=========================================")
    
    ov_acc = accuracy_score(y_true_all, y_pred_all)
    ov_prec, ov_rec, ov_f1, _ = precision_recall_fscore_support(y_true_all, y_pred_all, average='macro', zero_division=0)
    per_prec, per_rec, per_f1, _ = precision_recall_fscore_support(y_true_all, y_pred_all, labels=classes, average=None, zero_division=0)
    
    cm = confusion_matrix(y_true_all, y_pred_all, labels=classes)
    
    report_lines.append(f"Overall Accuracy:      {ov_acc:.4f}")
    report_lines.append(f"Overall Macro Precision: {ov_prec:.4f}")
    report_lines.append(f"Overall Macro Recall:    {ov_rec:.4f}")
    report_lines.append(f"Overall Macro F1:        {ov_f1:.4f}")
    
    report_lines.append("\n--- Per-Class (0, 5, 10) ---")
    report_lines.append(f"Precision: {np.round(per_prec, 4)}")
    report_lines.append(f"Recall:    {np.round(per_rec, 4)}")
    report_lines.append(f"F1 Score:  {np.round(per_f1, 4)}")
    
    report_lines.append("\n--- Confusion Matrix (0, 5, 10) ---")
    for row in cm:
        report_lines.append(str(row))
        
    # 10. Save Evaluation
    with open(report_out_path, 'w') as f:
        f.write("\n".join(report_lines))
        
    # 11. Save Confusion Matrix JSON
    cm_dict = {
        "labels": classes,
        "matrix": cm.tolist()
    }
    with open(cm_out_path, 'w') as f:
        json.dump(cm_dict, f, indent=2)
        
    # 12. Final Model (Train on ALL 743 windows)
    final_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    final_pipeline.fit(X, y)
    joblib.dump(final_pipeline, final_model_path)
    
    print("\n".join(report_lines))
    print(f"\nSaved final model to: {final_model_path}")

if __name__ == "__main__":
    train_loso()
