import pymongo
import gridfs
import os

def store_video_in_db(db, video_file_path, metadata):
    fs = gridfs.GridFS(db)  # Create a GridFS object
    with open(video_file_path, 'rb') as video_file:
        video_data = video_file.read()
        # Store video data in GridFS
        fs.put(video_data, filename=os.path.basename(video_file_path), metadata=metadata)

def connect_to_db():
    # Database connection
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['video_clips_db']  # Connect to the MongoDB database
    return db
