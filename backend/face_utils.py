import face_recognition
import cv2
import numpy as np
from PIL import Image
import base64
from io import BytesIO

def encode_face_from_image(image_data: str) -> list:
    """Encode face from base64 image data"""
    try:
        # Decode base64 image
        image_data = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Convert RGB to BGR for OpenCV
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        # Detect faces
        face_locations = face_recognition.face_locations(image_bgr)
        face_encodings = face_recognition.face_encodings(image_bgr, face_locations)
        
        if not face_encodings:
            raise ValueError("No face detected in image")
        
        # Return the first face encoding as a list
        return face_encodings[0].tolist()
        
    except Exception as e:
        raise ValueError(f"Error encoding face: {str(e)}")

def compare_faces(known_encoding: list, unknown_encoding: list, tolerance: float = 0.6) -> bool:
    """Compare two face encodings"""
    try:
        known_array = np.array(known_encoding)
        unknown_array = np.array(unknown_encoding)
        
        matches = face_recognition.compare_faces(
            [known_array], 
            unknown_array, 
            tolerance=tolerance
        )
        
        return matches[0]
        
    except Exception as e:
        raise ValueError(f"Error comparing faces: {str(e)}")

def detect_faces_in_image(image_data: str) -> list:
    """Detect all faces in an image and return their encodings"""
    try:
        # Decode base64 image
        image_data = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Convert RGB to BGR for OpenCV
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        # Detect faces
        face_locations = face_recognition.face_locations(image_bgr)
        face_encodings = face_recognition.face_encodings(image_bgr, face_locations)
        
        return [encoding.tolist() for encoding in face_encodings]
        
    except Exception as e:
        raise ValueError(f"Error detecting faces: {str(e)}")

def validate_face_image(image_data: str) -> bool:
    """Validate that an image contains exactly one face"""
    try:
        encodings = detect_faces_in_image(image_data)
        return len(encodings) == 1
    except:
        return False 