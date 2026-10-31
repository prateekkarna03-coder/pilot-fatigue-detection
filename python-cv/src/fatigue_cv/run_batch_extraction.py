import os
import glob
import logging
from fatigue_cv.dataset_extractor import DatasetExtractor
from fatigue_cv.prediction.window_aggregator import create_windows

logging.basicConfig(level=logging.INFO)

def find_kss_videos(subject_dir: str):
    """
    Given a subject directory, locate the 0, 5, and 10 KSS videos.
    Returns a list of tuples: [(path, "subject_id", kss_label)]
    """
    subject_id = os.path.basename(subject_dir)
    videos = []
    
    for kss in [0, 5, 10]:
        # Handle case-insensitive suffix for .mov and .MOV
        matches = glob.glob(os.path.join(subject_dir, f"{kss}.*"))
        mov_match = [m for m in matches if m.lower().endswith('.mov')]
        if mov_match:
            videos.append((mov_match[0], subject_id, kss))
        else:
            logging.warning(f"Could not find KSS {kss} video for Subject {subject_id}")
            
    return videos

def process_batch(base_dir: str = r"E:\UTA-RLDD\Fold1_part1", 
                  out_dir: str = r"E:\UTA-RLDD\extracted-features",
                  subjects_to_include: list = ["02", "03", "04", "05"]):
    """
    Run the batch extraction and windowing for the specified subjects.
    Does not process subjects outside of subjects_to_include list.
    Resumable: Skips extraction if the features output already exists.
    """
    os.makedirs(out_dir, exist_ok=True)
    
    extractor = DatasetExtractor()
    
    try:
        for subj in subjects_to_include:
            subj_dir = os.path.join(base_dir, subj)
            if not os.path.exists(subj_dir):
                logging.error(f"Subject directory not found: {subj_dir}")
                continue
                
            logging.info(f"--- Processing Subject {subj} ---")
            
            feat_csv = os.path.join(out_dir, f"subject_{subj}_features_v2.csv")
            win_csv  = os.path.join(out_dir, f"subject_{subj}_windows.csv")
            
            # 1. Extraction Pipeline
            if os.path.exists(feat_csv):
                logging.info(f"[{subj}] Features CSV already exists. Skipping extraction phase.")
                did_extract = False
            else:
                videos = find_kss_videos(subj_dir)
                if not videos:
                    logging.warning(f"[{subj}] No videos found. Skipping subject.")
                    continue
                
                logging.info(f"[{subj}] Extracting features from {len(videos)} videos...")
                extractor.extract_and_save(videos, feat_csv)
                did_extract = True
            
            # 2. Window Aggregation Pipeline
            if os.path.exists(win_csv) and not did_extract:
                logging.info(f"[{subj}] Windows CSV already exists and features weren't updated. Skipping windowing phase.")
            else:
                if os.path.exists(feat_csv):
                    logging.info(f"[{subj}] Generating 10-second temporal ML windows...")
                    create_windows(feat_csv, win_csv)
                else:
                    logging.error(f"[{subj}] Feature CSV is missing, cannot generate windows.")
                    
        logging.info("Batch processing complete.")
    finally:
        extractor.close()

if __name__ == "__main__":
    process_batch()
