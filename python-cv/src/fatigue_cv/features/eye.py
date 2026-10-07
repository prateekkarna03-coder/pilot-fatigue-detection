from ..detection.types import FaceLandmarks

# MediaPipe Eye indices (using normalized index array layout)
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def euclidean_distance(p1, p2) -> float:
    return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2)**0.5

def _eye_aspect_ratio(eye_indices, landmarks: FaceLandmarks) -> float:
    if not landmarks or len(landmarks.points) < 478:
        return 0.0
        
    p1 = landmarks.points[eye_indices[0]] 
    p2 = landmarks.points[eye_indices[1]] 
    p3 = landmarks.points[eye_indices[2]] 
    p4 = landmarks.points[eye_indices[3]] 
    p5 = landmarks.points[eye_indices[4]] 
    p6 = landmarks.points[eye_indices[5]] 

    v1 = euclidean_distance(p2, p6)
    v2 = euclidean_distance(p3, p5)
    h = euclidean_distance(p1, p4)
    
    if h == 0.0:
        return 0.0
        
    return (v1 + v2) / (2.0 * h)

def calculate_eye_ears(landmarks: FaceLandmarks) -> tuple[float, float]:
    """Calculate the left and right Eye Aspect Ratios."""
    left_ear = _eye_aspect_ratio(LEFT_EYE, landmarks)
    right_ear = _eye_aspect_ratio(RIGHT_EYE, landmarks)
    return left_ear, right_ear

def calculate_ear(landmarks: FaceLandmarks) -> float:
    """Calculate average Eye Aspect Ratio using generic landmarks."""
    left_ear, right_ear = calculate_eye_ears(landmarks)
    return (left_ear + right_ear) / 2.0
