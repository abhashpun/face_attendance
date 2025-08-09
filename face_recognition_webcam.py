import cv2
import face_recognition
import os
import numpy as np
from datetime import datetime
import time
import pickle

class FaceRecognitionSystem:
    def __init__(self):
        self.known_faces_dir = "known_faces"
        self.encodings_file = "face_encodings.pkl"
        self.known_encodings = []
        self.known_names = []
        self.attendance_file = "attendance.csv"
        self.attendance_logged = set()
        self.video_capture = None
        
        # Performance optimization settings
        self.process_every_n_frames = 3  # Process every 3rd frame
        self.frame_count = 0
        self.last_face_locations = []
        self.last_face_names = []
        self.last_processing_time = 0
        
        # Create known_faces directory if it doesn't exist
        if not os.path.exists(self.known_faces_dir):
            os.makedirs(self.known_faces_dir)
            print(f"Created {self.known_faces_dir} directory")
            print("Please add face images (.jpg or .png) to this directory")
            print("Use the person's name as the filename (without extension)")
        
        self.load_known_faces()
    
    def save_encodings_to_file(self):
        """Save face encodings and names to a pickle file"""
        try:
            data = {
                'encodings': self.known_encodings,
                'names': self.known_names,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(data, f)
            print(f"✓ Encodings saved to {self.encodings_file}")
        except Exception as e:
            print(f"✗ Error saving encodings: {e}")
    
    def load_encodings_from_file(self):
        """Load face encodings and names from pickle file"""
        try:
            if os.path.exists(self.encodings_file):
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                self.known_encodings = data['encodings']
                self.known_names = data['names']
                print(f"✓ Loaded {len(self.known_names)} encodings from {self.encodings_file}")
                print(f"  Last updated: {data.get('timestamp', 'Unknown')}")
                return True
        except Exception as e:
            print(f"✗ Error loading encodings: {e}")
        return False
    
    def check_if_encodings_need_update(self):
        """Check if encodings need to be regenerated based on file changes"""
        if not os.path.exists(self.encodings_file):
            return True
        
        try:
            # Get modification time of encodings file
            encodings_mtime = os.path.getmtime(self.encodings_file)
            
            # Check if any face image is newer than the encodings file
            for filename in os.listdir(self.known_faces_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(self.known_faces_dir, filename)
                    image_mtime = os.path.getmtime(image_path)
                    if image_mtime > encodings_mtime:
                        print(f"✓ Face image {filename} is newer than encodings, will regenerate")
                        return True
            
            return False
        except Exception as e:
            print(f"✗ Error checking file timestamps: {e}")
            return True
    
    def load_known_faces(self):
        """Load all known faces from the known_faces directory or cached encodings"""
        print("Loading known faces...")
        
        if not os.path.exists(self.known_faces_dir):
            print(f"Directory {self.known_faces_dir} does not exist!")
            return
        
        # Try to load cached encodings first
        if self.load_encodings_from_file():
            # Check if encodings need to be updated
            if not self.check_if_encodings_need_update():
                print(f"✓ Using cached encodings for {len(self.known_names)} faces")
                return
        
        # If we reach here, we need to regenerate encodings
        print("Regenerating face encodings...")
        self.known_encodings = []
        self.known_names = []
        
        for filename in os.listdir(self.known_faces_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                try:
                    image_path = os.path.join(self.known_faces_dir, filename)
                    image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(image)
                    
                    if len(encodings) > 0:
                        self.known_encodings.append(encodings[0])
                        name = os.path.splitext(filename)[0]
                        self.known_names.append(name)
                        print(f"✓ Generated encoding for: {name}")
                    else:
                        print(f"✗ No face detected in {filename}")
                        
                except Exception as e:
                    print(f"✗ Error processing {filename}: {e}")
        
        # Save the new encodings to file
        if len(self.known_encodings) > 0:
            self.save_encodings_to_file()
            print(f"\nSuccessfully generated and saved {len(self.known_names)} face encodings")
        else:
            print("\nNo faces loaded. Please add face images to the known_faces directory.")
    
    def mark_attendance(self, name):
        """Mark attendance for a recognized person"""
        if name not in self.attendance_logged:
            with open(self.attendance_file, "a") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{name},{timestamp}\n")
            self.attendance_logged.add(name)
            print(f"✓ Attendance marked for: {name}")
    
    def process_frame_optimized(self, frame):
        """Process a single frame with optimizations for better performance"""
        self.frame_count += 1
        
        # Only process every nth frame to reduce lag
        if self.frame_count % self.process_every_n_frames != 0:
            # Use cached results for display
            return self.draw_faces_on_frame(frame, self.last_face_locations, self.last_face_names)
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize frame for faster processing (optional)
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
        
        # Find faces in the frame
        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)
        
        # Scale back the face locations to original size
        face_locations = [(top * 4, right * 4, bottom * 4, left * 4) for top, right, bottom, left in face_locations]
        
        # Process each face found
        face_names = []
        for face_encoding in face_encodings:
            name = "Unknown"
            
            if len(self.known_encodings) > 0:
                # Compare with known faces
                matches = face_recognition.compare_faces(self.known_encodings, face_encoding, tolerance=0.6)
                
                if True in matches:
                    match_index = matches.index(True)
                    name = self.known_names[match_index]
                    self.mark_attendance(name)
            
            face_names.append(name)
        
        # Cache results for next frames
        self.last_face_locations = face_locations
        self.last_face_names = face_names
        
        return self.draw_faces_on_frame(frame, face_locations, face_names)
    
    def draw_faces_on_frame(self, frame, face_locations, face_names):
        """Draw face rectangles and names on frame"""
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            
            # Draw rectangle around face
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw name label
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def add_ui_info(self, frame):
        """Add UI information to the frame"""
        # Add instructions
        cv2.putText(frame, "Press 'q' to quit, 's' to save frame", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add performance info
        fps_info = f"Processing: 1/{self.process_every_n_frames} frames"
        cv2.putText(frame, fps_info, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add face count
        face_count = len(self.last_face_locations)
        cv2.putText(frame, f"Faces detected: {face_count}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add known faces count
        cv2.putText(frame, f"Known faces: {len(self.known_names)}", (10, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add encoding status
        encoding_status = "Cached" if os.path.exists(self.encodings_file) else "Generated"
        cv2.putText(frame, f"Encodings: {encoding_status}", (10, 150),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def save_frame(self, frame):
        """Save current frame as image"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captured_frame_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        print(f"✓ Frame saved as: {filename}")
    
    def run(self):
        """Main loop for face recognition with performance optimizations"""
        print("Initializing camera...")
        self.video_capture = cv2.VideoCapture(0)
        
        # Set camera properties for better performance
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.video_capture.set(cv2.CAP_PROP_FPS, 30)
        
        if not self.video_capture.isOpened():
            print("Error: Could not open camera!")
            return
        
        print("Camera initialized successfully!")
        print(f"Performance mode: Processing every {self.process_every_n_frames} frames")
        print("Press 'q' to quit, 's' to save current frame")
        print("Press '1-9' to adjust processing frequency (1=every frame, 9=every 9th frame)")
        print("Press 'r' to regenerate encodings")
        print("Starting face recognition...")
        
        try:
            while True:
                ret, frame = self.video_capture.read()
                if not ret:
                    print("Error: Could not read frame from camera!")
                    break
                
                # Process frame for face recognition
                frame = self.process_frame_optimized(frame)
                
                # Add UI information
                frame = self.add_ui_info(frame)
                
                # Display the frame
                cv2.imshow("Face Recognition System", frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Quitting...")
                    break
                elif key == ord('s'):
                    self.save_frame(frame)
                elif key == ord('r'):
                    print("Regenerating encodings...")
                    self.load_known_faces()
                elif key in [ord(str(i)) for i in range(1, 10)]:
                    # Adjust processing frequency
                    new_freq = int(chr(key))
                    self.process_every_n_frames = new_freq
                    print(f"Processing frequency changed to: every {new_freq} frames")
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.video_capture:
            self.video_capture.release()
        cv2.destroyAllWindows()
        print("Face recognition system closed.")

def main():
    print("=== Face Recognition System (Optimized with Cached Encodings) ===")
    print("Using your webcam for real-time face recognition")
    print("Face encodings are cached for faster startup and inference")
    print()
    
    # Create and run the face recognition system
    face_system = FaceRecognitionSystem()
    face_system.run()

if __name__ == "__main__":
    main() 