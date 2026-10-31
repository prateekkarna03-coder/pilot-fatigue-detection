import csv
import statistics
import os

def create_windows(input_csv: str, output_csv: str, window_duration: float = 10.0):
    """
    Groups frame-level data by video_name and creates fixed temporal windows.
    Generates one ML sample per window with summary statistics.
    Assumes missing values are denoted by empty strings or 'None'.
    """
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    with open(input_csv, 'r', newline='') as f_in, open(output_csv, 'w', newline='') as f_out:
        reader = csv.DictReader(f_in)
        
        headers = [
            'subject_id', 'video_name', 'kss_label', 'window_id',
            'ear_mean', 'ear_min',
            'mar_mean', 'mar_max',
            'blink_rate_mean', 'blink_rate_max',
            'yawn_rate_mean', 'yawn_rate_max',
            'closure_duration_max',
            'pitch_median', 'pitch_std',
            'yaw_median', 'yaw_std',
            'roll_median', 'roll_std'
        ]
        
        writer = csv.DictWriter(f_out, fieldnames=headers)
        writer.writeheader()
        
        current_video = None
        current_window_idx = -1
        window_rows = []
        
        def process_window():
            if not window_rows:
                return
                
            def get_valid_floats(key):
                res = []
                for row in window_rows:
                    val = row.get(key)
                    if val and str(val).strip().lower() != 'none':
                        try:
                            res.append(float(val))
                        except ValueError:
                            pass
                return res
                
            ears = get_valid_floats('ear')
            mars = get_valid_floats('mar')
            blink_rates = get_valid_floats('blink_rate_per_minute')
            yawn_rates = get_valid_floats('yawn_rate_per_minute')
            closures = get_valid_floats('current_closure_duration')
            pitches = get_valid_floats('pitch')
            yaws = get_valid_floats('yaw')
            rolls = get_valid_floats('roll')
            
            def agg(items, func):
                if len(items) == 0:
                    return "" # Write empty string for missing
                if func == statistics.stdev and len(items) < 2:
                    return 0.0 # Stdev is 0 if only 1 item
                return round(func(items), 4)
                
            row = {
                'subject_id': window_rows[0]['subject_id'],
                'video_name': window_rows[0]['video_name'],
                'kss_label': window_rows[0]['kss_label'],
                'window_id': current_window_idx,
                'ear_mean': agg(ears, statistics.mean),
                'ear_min': agg(ears, min),
                'mar_mean': agg(mars, statistics.mean),
                'mar_max': agg(mars, max),
                'blink_rate_mean': agg(blink_rates, statistics.mean),
                'blink_rate_max': agg(blink_rates, max),
                'yawn_rate_mean': agg(yawn_rates, statistics.mean),
                'yawn_rate_max': agg(yawn_rates, max),
                'closure_duration_max': agg(closures, max),
                'pitch_median': agg(pitches, statistics.median),
                'pitch_std': agg(pitches, statistics.stdev),
                'yaw_median': agg(yaws, statistics.median),
                'yaw_std': agg(yaws, statistics.stdev),
                'roll_median': agg(rolls, statistics.median),
                'roll_std': agg(rolls, statistics.stdev),
            }
            writer.writerow(row)
        
        for r in reader:
            vid = r.get('video_name')
            ts_str = r.get('timestamp')
            
            if not ts_str:
                continue
                
            ts = float(ts_str)
            win_idx = int(ts // window_duration)
            
            if vid != current_video or win_idx != current_window_idx:
                if current_video is not None:
                    process_window()
                window_rows = []
                current_video = vid
                current_window_idx = win_idx
                
            window_rows.append(r)
            
        if window_rows:
            process_window()

if __name__ == '__main__':
    inp = r"E:\UTA-RLDD\extracted-features\subject_01_features_v2.csv"
    out = r"E:\UTA-RLDD\extracted-features\subject_01_windows.csv"
    create_windows(inp, out)
