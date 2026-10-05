from ..detection.types import FaceLandmarks

def euclidean_distance(p1, p2) -> float:
    return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2)**0.5

def calculate_mar(landmarks: FaceLandmarks) -> float:
    """Calculate Mouth Aspect Ratio."""
    if not landmarks or len(landmarks.points) < 478:
        return 0.0
        
    h_dist = euclidean_distance(landmarks.points[61], landmarks.points[291])
    v_dist = euclidean_distance(landmarks.points[13], landmarks.points[14])
    
    if h_dist == 0.0:
        return 0.0
        
    return v_dist / h_dist
