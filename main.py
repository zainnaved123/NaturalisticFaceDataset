from face_extractor import extract_faces_from_video
from pipeline import connect_to_db

# Connect to the database
db = connect_to_db()

# Call the face extraction function
extract_faces_from_video("test3.mp4", "extracted_clips", confidence_threshold=0.5, frame_interval=5, clip_duration=4, db=db)
