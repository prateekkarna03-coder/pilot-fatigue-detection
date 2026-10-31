import pytest
import os
import csv
import tempfile
from fatigue_cv.prediction.window_aggregator import create_windows

def test_create_windows_basic():
    # Setup mock CSV contents
    input_data = [
        {"subject_id": "01", "video_name": "0.mov", "kss_label": "0", "timestamp": "0.0", "ear": "0.30", "mar": "0.05", "blink_rate_per_minute": "0", "yawn_rate_per_minute": "0", "current_closure_duration": "0", "pitch": "10.0", "yaw": "0.0", "roll": "0.0"},
        {"subject_id": "01", "video_name": "0.mov", "kss_label": "0", "timestamp": "5.0", "ear": "0.20", "mar": "0.05", "blink_rate_per_minute": "10", "yawn_rate_per_minute": "0", "current_closure_duration": "0", "pitch": "12.0", "yaw": "0.0", "roll": "0.0"},
        
        # Second window
        {"subject_id": "01", "video_name": "0.mov", "kss_label": "0", "timestamp": "12.0", "ear": "0.25", "mar": "0.05", "blink_rate_per_minute": "15", "yawn_rate_per_minute": "0", "current_closure_duration": "0", "pitch": "10.0", "yaw": "0.0", "roll": "0.0"},
        
        # Second video (resets window chunking)
        {"subject_id": "01", "video_name": "5.mov", "kss_label": "5", "timestamp": "0.0", "ear": "0.20", "mar": "0.30", "blink_rate_per_minute": "5", "yawn_rate_per_minute": "1", "current_closure_duration": "0", "pitch": "0.0", "yaw": "0.0", "roll": "0.0"},
        
        # Missing values row
        {"subject_id": "01", "video_name": "5.mov", "kss_label": "5", "timestamp": "1.0", "ear": "", "mar": "None", "blink_rate_per_minute": "", "yawn_rate_per_minute": "1", "current_closure_duration": "0", "pitch": "", "yaw": "", "roll": ""},
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', newline='', delete=False) as f_in, tempfile.NamedTemporaryFile(mode='w', newline='', delete=False) as f_out:
        in_path = f_in.name
        out_path = f_out.name
        
        writer = csv.DictWriter(f_in, fieldnames=input_data[0].keys())
        writer.writeheader()
        writer.writerows(input_data)
        
    try:
        # Run conversion
        create_windows(in_path, out_path, window_duration=10.0)
        
        with open(out_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # We expect 3 windows: 0.mov win 0, 0.mov win 1, 5.mov win 0
            assert len(rows) == 3
            
            # Check First window aggregations
            w1 = rows[0]
            assert w1['video_name'] == '0.mov'
            assert w1['window_id'] == '0'
            assert w1['kss_label'] == '0'
            assert float(w1['ear_mean']) == 0.25  # mean of 0.30 and 0.20
            assert float(w1['ear_min']) == 0.20
            assert float(w1['blink_rate_max']) == 10.0
            assert float(w1['pitch_median']) == 11.0 # median of 10 and 12
            assert float(w1['pitch_std']) > 0.0 # stdev > 0
            
            # Check Second window
            w2 = rows[1]
            assert w2['video_name'] == '0.mov'
            assert w2['window_id'] == '1'
            assert float(w2['ear_mean']) == 0.25
            assert float(w2['pitch_std']) == 0.0 # only 1 element, stdev is 0
            
            # Check Third window (missing value handling)
            w3 = rows[2]
            assert w3['video_name'] == '5.mov'
            assert w3['window_id'] == '0'
            assert w3['kss_label'] == '5'
            assert float(w3['ear_mean']) == 0.20 # Ignore the empty string
            assert float(w3['yawn_rate_max']) == 1.0 
    finally:
        os.remove(in_path)
        os.remove(out_path)
