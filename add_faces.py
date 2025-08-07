import cv2
import os
import face_recognition

def capture_face(name):
    """Capture a face image using webcam"""
    print(f"Capturing face for: {name}")
    print("Position your face in the camera and press 'c' to capture")
    print("Press 'q' to quit without capturing")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera!")
        return False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame!")
            break
        
        # Convert to RGB for face detection
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        # Draw rectangle around detected face
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, "Face Detected", (left, top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Add instructions
        cv2.putText(frame, "Press 'c' to capture, 'q' to quit", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Capturing for: {name}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow("Capture Face", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Cancelled capture")
            break
        elif key == ord('c'):
            if len(face_locations) > 0:
                # Save the captured image
                filename = f"{name}.jpg"
                filepath = os.path.join("known_faces", filename)
                cv2.imwrite(filepath, frame)
                print(f"✓ Face captured and saved as: {filepath}")
                break
            else:
                print("No face detected! Please position your face in the camera.")
    
    cap.release()
    cv2.destroyAllWindows()
    return True

def main():
    print("=== Face Capture Tool ===")
    print("This tool helps you capture face images for the recognition system")
    print()
    
    # Create known_faces directory if it doesn't exist
    if not os.path.exists("known_faces"):
        os.makedirs("known_faces")
        print("Created 'known_faces' directory")
    
    while True:
        print("\nOptions:")
        print("1. Add a new face")
        print("2. List existing faces")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            name = input("Enter the person's name: ").strip()
            if name:
                capture_face(name)
            else:
                print("Name cannot be empty!")
        
        elif choice == '2':
            if os.path.exists("known_faces"):
                files = [f for f in os.listdir("known_faces") 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if files:
                    print("\nExisting faces:")
                    for file in files:
                        name = os.path.splitext(file)[0]
                        print(f"  - {name}")
                else:
                    print("\nNo faces found in known_faces directory")
            else:
                print("\nknown_faces directory does not exist")
        
        elif choice == '3':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice! Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main() 