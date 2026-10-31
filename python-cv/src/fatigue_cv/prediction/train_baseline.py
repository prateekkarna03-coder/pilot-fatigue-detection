import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import joblib

def train_baseline(dataset_path: str = r"E:\UTA-RLDD\extracted-features\subject_01_windows.csv",
                   model_out_path: str = r"E:\UTA-RLDD\models\fatigue_baseline_subject01.joblib",
                   report_out_path: str = r"E:\UTA-RLDD\models\fatigue_baseline_report.txt"):
    os.makedirs(os.path.dirname(model_out_path), exist_ok=True)
    os.makedirs(os.path.dirname(report_out_path), exist_ok=True)

    # 1. Load Data
    df = pd.read_csv(dataset_path)

    # 2. Target and Features
    target_col = "kss_label"
    feature_cols = [
        "ear_mean", "ear_min", "mar_mean", "mar_max",
        "blink_rate_mean", "blink_rate_max", "yawn_rate_mean", "yawn_rate_max",
        "closure_duration_max", "pitch_median", "pitch_std",
        "yaw_median", "yaw_std", "roll_median", "roll_std"
    ]

    # Drop any row that doesn't at least have a target or video_name
    df = df.dropna(subset=[target_col, "video_name"]).reset_index(drop=True)

    X = df[feature_cols]
    y = df[target_col]
    groups = df["video_name"]

    # 7. Grouped Split By Video
    # We will use GroupShuffleSplit. Note that since there are only 3 videos (one per class), 
    # the test set will end up lacking representation from the training classes, 
    # which highlights the exact academic limitation of single-subject validation.
    gss = GroupShuffleSplit(n_splits=1, test_size=0.33, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups))

    X_train, y_train, groups_train = X.iloc[train_idx], y.iloc[train_idx], groups.iloc[train_idx]
    X_test, y_test, groups_test = X.iloc[test_idx], y.iloc[test_idx], groups.iloc[test_idx]

    # 4 & 5. Pipeline with Imputation and Random Forest
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])

    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    
    # 8. Report metrics
    acc = accuracy_score(y_test, y_pred)
    # Note: Because the test set might only have 1 class entirely missing from train,
    # precision/recall will be 0.0 with warnings. Zero_division=0 gracefully handles this.
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)
    
    # Per-class metrics over unique classes in y
    # To get a consistent reporting, we map over all possible classes: 0, 5, 10
    classes = [0, 5, 10]
    prec_per, rec_per, f1_per, _ = precision_recall_fscore_support(y_test, y_pred, labels=classes, average=None, zero_division=0)
    
    cm = confusion_matrix(y_test, y_pred, labels=classes)

    # 9. Save Model
    joblib.dump(pipeline, model_out_path)

    # 10. Save Evaluation
    report = []
    report.append("=========================================")
    report.append("ACADEMIC BASELINE VALIDATION - SUBJECT 01")
    report.append("=========================================")
    report.append(f"Train windows: {len(X_train)}")
    report.append(f"Test windows: {len(X_test)}")
    report.append(f"Train videos: {groups_train.unique().tolist()}")
    report.append(f"Test videos: {groups_test.unique().tolist()}")
    report.append(f"Train class distribution:\n{y_train.value_counts().to_dict()}")
    report.append(f"Test class distribution:\n{y_test.value_counts().to_dict()}")
    report.append("")
    report.append("--- Metrics ---")
    report.append(f"Accuracy:      {acc:.4f}")
    report.append(f"Macro Precision: {prec_macro:.4f}")
    report.append(f"Macro Recall:    {rec_macro:.4f}")
    report.append(f"Macro F1 Score:  {f1_macro:.4f}")
    report.append("")
    report.append("--- Per-Class (0, 5, 10) ---")
    report.append(f"Precision: {prec_per}")
    report.append(f"Recall:    {rec_per}")
    report.append(f"F1 Score:  {f1_per}")
    report.append("")
    report.append("--- Confusion Matrix (0, 5, 10) ---")
    for row in cm:
        report.append(str(row))
    report.append("")
    report.append("--- Output Model ---")
    report.append(model_out_path)

    with open(report_out_path, 'w') as f:
        f.write("\n".join(report))

    print("\n".join(report))

if __name__ == "__main__":
    train_baseline()
