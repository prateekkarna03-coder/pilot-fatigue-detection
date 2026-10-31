import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def combine_and_validate(base_dir: str = r"E:\UTA-RLDD\extracted-features",
                         output_file: str = r"E:\UTA-RLDD\extracted-features\all_subjects_windows.csv",
                         subjects: list = ["01", "02", "03", "04", "05"]):
    
    all_dfs = []
    base_columns = None
    
    # 1 & 3: Load requested subjects
    missing_subjects = []
    for subj in subjects:
        file_path = os.path.join(base_dir, f"subject_{subj}_windows.csv")
        if not os.path.exists(file_path):
            missing_subjects.append(subj)
            continue
            
        df = pd.read_csv(file_path)
        
        # 5: Schema consistency validation
        if base_columns is None:
            base_columns = list(df.columns)
        else:
            if list(df.columns) != base_columns:
                raise ValueError(f"Schema mismatch in subject {subj}. Expected {base_columns}, got {list(df.columns)}")
                
        all_dfs.append(df)
        
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # 5: Validations
    
    # Total row count
    total_rows = len(combined_df)
    
    # Windows per subject
    # Format properly for output
    windows_per_subject = combined_df['subject_id'].value_counts().to_dict()
    
    # KSS counts
    kss_counts = combined_df['kss_label'].value_counts().to_dict()
    
    # Check that every subject has all three KSS classes (only for present subjects)
    expected_kss = {0, 5, 10}
    for subj in [s for s in subjects if s not in missing_subjects]:
        subj_kss = set(combined_df[combined_df['subject_id'] == int(subj)]['kss_label'].unique())
        # Handles case if subject_id is parsed as string vs int
        if len(subj_kss) == 0:
            subj_kss = set(combined_df[combined_df['subject_id'] == subj]['kss_label'].unique())
            
        if subj_kss != expected_kss:
            raise ValueError(f"Subject {subj} does not have all KSS classes! Found: {subj_kss}")
            
    # Duplicate rows/windows validation
    # A window is uniquely identified by (subject_id, video_name, window_id)
    duplicates = combined_df.duplicated(subset=['subject_id', 'video_name', 'window_id'])
    duplicate_count = int(duplicates.sum())
    if duplicate_count > 0:
        raise ValueError(f"Found {duplicate_count} duplicate window identifiers!")
        
    # Missing numerical values
    feature_cols = [c for c in base_columns if c not in ('subject_id', 'video_name', 'kss_label', 'window_id')]
    missing_values = combined_df[feature_cols].isna().sum().to_dict()
    total_missing = sum(missing_values.values())
    
    # Save the combined dataset (Requirement 1 & 4)
    combined_df.to_csv(output_file, index=False)
    
    # Print the requested report exactly
    report = []
    report.append("=========================================")
    report.append("DATASET COMBINATION & VALIDATION REPORT")
    report.append("=========================================")
    report.append(f"Output path: {output_file}")
    report.append(f"Total windows: {total_rows}")
    report.append("Windows per subject:")
    for k, v in windows_per_subject.items():
        report.append(f"  Subject {k}: {v}")
    report.append("KSS distribution:")
    for k, v in kss_counts.items():
        report.append(f"  KSS {k}: {v}")
    if missing_subjects:
        report.append(f"WARNING: The following subjects were MISSING from disk: {missing_subjects}")
    else:
        report.append("Missing Subjects: NONE")
    report.append(f"Missing values (across features): {total_missing}")
    if total_missing > 0:
        for k, v in missing_values.items():
            if v > 0:
                report.append(f"   - {k}: {v}")
                
    report.append(f"Duplicate count: {duplicate_count}")
    report.append("Schema validation: PASSED (Consistent across all files)")
    if missing_subjects:
        report.append("Subject KSS Completeness: PARTIAL (Skipped missing subjects, remaining have 0, 5, 10)")
    else:
        report.append("Subject KSS Completeness: PASSED (All subjects have 0, 5, 10)")
    
    report_str = "\n".join(report)
    print(report_str)
    
    # Return metrics for testing purposes
    return {
        "total_rows": total_rows,
        "duplicate_count": duplicate_count,
        "total_missing": total_missing,
        "schema_valid": True
    }

if __name__ == "__main__":
    try:
        combine_and_validate()
    except Exception as e:
        with open("clean_error.txt", "w") as f:
            f.write(str(e))
