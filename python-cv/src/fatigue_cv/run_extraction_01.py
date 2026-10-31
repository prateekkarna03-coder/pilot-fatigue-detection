# c:\Users\prate\Desktop\Semester\5 Sem\Ai\Project\pilot-fatigue-system\python-cv\src\fatigue_cv\run_extraction_01.py
import logging
import os
from fatigue_cv.dataset_extractor import DatasetExtractor

logging.basicConfig(level=logging.INFO)

def main():
    base_dir = r"E:\UTA-RLDD\Fold1_part1\01"
    output_csv = r"E:\UTA-RLDD\extracted-features\subject_01_features_v2.csv"
    
    # We configure paths, subject ID, and KSS rating
    # 0.mov = KSS 0
    # 5.mov = KSS 5
    # 10.MOV = KSS 10
    
    videos_to_process = [
        (os.path.join(base_dir, "0.mov"), "01", 0),
        (os.path.join(base_dir, "5.mov"), "01", 5),
        (os.path.join(base_dir, "10.MOV"), "01", 10),
    ]
    
    # Check if files actually exist before starting
    for vpath, _, _ in videos_to_process:
        if not os.path.exists(vpath):
            logging.warning(f"Video file not found: {vpath} - are you sure the drive is connected?")
    
    extractor = DatasetExtractor()
    try:
        extractor.extract_and_save(videos_to_process, output_csv)
        logging.info(f"Extraction for Subject 01 complete. Output saved to {output_csv}")
    finally:
        extractor.close()

if __name__ == "__main__":
    main()
