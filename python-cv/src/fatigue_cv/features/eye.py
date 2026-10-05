from ..detection.types import FaceLandmarks

# MediaPipe Eye indices
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def euclidean_distance(p1, p2) -> float:
    return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2)**0.5

def calculate_ear(landmarks: FaceLandmarks) -> float:
    """Calculate Eye Aspect Ratio using generic landmarks."""
    # Simplified EAR for the stub, normally we'd compute both eyes and average.
    # In Step 5A, we just mock the computation structure.
    return 0.25 # stub return
