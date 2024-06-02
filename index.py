import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from collections import deque, defaultdict
import os
import json
from imdb import fetch_actors_from_movie
import requests


# Load the insightface model
def load_model():
    app = FaceAnalysis(name="buffalo_l", root="./insightface_model")
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app


# Initialize character embeddings dictionary
character_embeddings = {}
embedding_buffers = defaultdict(
    lambda: deque(maxlen=5)
)  # Buffer for averaging embeddings


def initialize_embeddings_from_movie(movie_name, app):
    actors = fetch_actors_from_movie(movie_name)
    if actors:
        for actor in actors:
            if actor["profile_image"]:
                img_resp = requests.get(actor["profile_image"])
                img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
                img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

                # Ensure image has 3 color channels
                if len(img.shape) == 2:  # Grayscale image
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                elif img.shape[2] == 1:  # Single channel image
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

                faces = app.get(img)
                if faces:
                    face = faces[0]
                    character_embeddings[actor["name"]] = face.normed_embedding
    return character_embeddings


# Function to find the closest character embedding
def recognize_face(face_embedding):
    min_dist = float("inf")
    label = "Unknown"
    for name, emb in character_embeddings.items():
        dist = np.linalg.norm(face_embedding - emb)
        if dist < min_dist:
            min_dist = dist
            label = name
    return label, min_dist


# Function to add a new character
def add_new_character(face_embedding, character_count):
    character_name = f"Character{character_count}"
    character_embeddings[character_name] = face_embedding
    character_count += 1
    return character_name, character_count


# Update embedding buffer and compute average embedding
def update_embedding_buffer(label, new_embedding):
    buffer = embedding_buffers[label]
    buffer.append(new_embedding)
    average_embedding = np.mean(buffer, axis=0)
    return average_embedding


# Ensure output directory exists
def ensure_output_dir(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


# Check if bounding box is within the frame
def is_bbox_within_frame(bbox, frame_width, frame_height):
    x, y, w, h = bbox
    return (
        0 <= x < frame_width
        and 0 <= y < frame_height
        and x + w <= frame_width
        and y + h <= frame_height
    )


# Handle a new face detected in the frame
def handle_new_face(face, frame, character_count, threshold):
    bbox = face.bbox.astype(int)
    x1, y1, x2, y2 = bbox
    face_embedding = face.normed_embedding

    # Adjust bounding box if needed
    width = x2 - x1
    height = y2 - y1

    # Check if width and height are reasonable
    if width <= 0 or height <= 0:
        return None, None, character_count, None, None, None, None

    # Optionally, adjust bounding box padding here if necessary
    padding = 50  # Adjust this value if needed
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(frame.shape[1], x2 + padding)
    y2 = min(frame.shape[0], y2 + padding)

    # Ensure bounding box is within frame
    if not is_bbox_within_frame(
        (x1, y1, x2 - x1, y2 - y1), frame.shape[1], frame.shape[0]
    ):
        return None, None, character_count, None, None, None, None

    # Process face embedding and recognition
    label, min_dist = recognize_face(face_embedding)
    if min_dist > threshold:
        label, character_count = add_new_character(face_embedding, character_count)

    # Update embedding buffer and compute average embedding
    average_embedding = update_embedding_buffer(label, face_embedding)

    # Optionally, get additional face attributes
    gender = face.gender
    age = face.age
    race = face.race
    smiling = face.smiling

    return (
        label,
        (x1, y1, x2 - x1, y2 - y1),
        character_count,
        gender,
        age,
        race,
        smiling,
    )


def clip_bbox(bbox, frame_width, frame_height):
    x, y, w, h = bbox
    x = max(0, x)
    y = max(0, y)
    w = min(w, frame_width - x)
    h = min(h, frame_height - y)
    return x, y, w, h


# Initialize tracker for the face
def initialize_tracker(
    frame, bbox, label, trackers, frame_buffers, clip_duration, frame_rate
):
    tracker = cv2.TrackerKCF_create()
    tracker.init(frame, bbox)

    trackers[label] = tracker
    print("int init", int(clip_duration * frame_rate))
    frame_buffers[label] = deque(maxlen=int(clip_duration * frame_rate))
    return True


def draw_labels(frame, trackers, frame_buffers):
    for label, bbox in trackers:
        x, y, w, h = bbox
        cv2.rectangle(
            frame, (x, y), (x + w, y + h), (255, 0, 0), 2
        )  # Draw bounding box
        cv2.putText(
            frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2
        )  # Label the face


def save_clip_info(clip_info, json_path):
    def convert_numpy(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    if os.path.exists(json_path):
        with open(json_path, "r") as file:
            data = json.load(file)
    else:
        data = []

    clip_info = {k: convert_numpy(v) for k, v in clip_info.items()}
    data.append(clip_info)

    with open(json_path, "w") as file:
        json.dump(data, file, indent=4)


def save_tracked_face_clips(
    label, frame_buffers, output_dir, clip_counter, clip_details, json_path
):
    print(
        label in frame_buffers, len(frame_buffers[label]) > 0, len(frame_buffers[label])
    )
    if label in frame_buffers and len(frame_buffers[label]) > 0:
        clip_frames = list(frame_buffers[label])
        height, width, _ = clip_frames[0].shape
        out_path = os.path.join(output_dir, f"clip{clip_counter}.mp4")
        out = cv2.VideoWriter(
            out_path, cv2.VideoWriter_fourcc(*"mp4v"), 30, (width, height)
        )

        for frame in clip_frames:
            out.write(frame)
        out.release()
        del frame_buffers[label]

        clip_info = {
            "clip_number": clip_counter,
            "character": label,
            "gender": clip_details[label]["gender"],
            "age": clip_details[label]["age"],
            "race": clip_details[label]["race"],
            "smiling": clip_details[label]["smiling"],
            "file_path": out_path,
        }
        save_clip_info(clip_info, json_path)

        clip_counter += 1
        print(f"Saved clip for {label} as {out_path}")

    return clip_counter


# Remove old trackers and save clips if the face is no longer present
def remove_old_trackers(
    trackers,
    frame_buffers,
    current_trackers,
    frame_rate,
    frame_width,
    frame_height,
    output_dir,
    clip_counter,
    clip_details,
    json_path,
):
    current_labels = set(label for label, _ in current_trackers)
    old_labels = set(trackers.keys()) - current_labels

    for label in old_labels:
        print("old label: ", label, "saving clip")
        clip_counter = save_tracked_face_clips(
            label, frame_buffers, output_dir, clip_counter, clip_details, json_path
        )
        del trackers[label]

    return clip_counter


# Process the video
def process_video(
    video_path, app, output_dir, json_path, threshold=1.0, clip_duration=5
):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video stream or file: {video_path}")
        return

    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    print("frame rate", frame_rate)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    trackers = {}
    frame_buffers = defaultdict(deque)
    clip_details = {}
    clip_counter = 0
    current_trackers = []

    cap = cv2.VideoCapture(video_path)
    character_count = 1
    clip_counter = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = app.get(frame)

        next_trackers = []

        for face in faces:
            label, bbox, character_count, gender, age, race, smiling = handle_new_face(
                face, frame, character_count, threshold
            )
            if bbox is None:
                continue  # Skip if bbox is None

            # bbox is already a tuple or list, no need to convert it
            bbox = list(bbox)

            clip_details[label] = {
                "gender": gender,
                "age": age,
                "race": race,
                "smiling": smiling,
            }

            if label not in trackers:
                success = initialize_tracker(
                    frame, bbox, label, trackers, frame_buffers, 5, frame_rate
                )
                if success:
                    next_trackers.append((label, bbox))
            else:
                success, new_bbox = trackers[label].update(frame)
                if success:
                    next_trackers.append((label, list(map(int, new_bbox))))

                    # Extract ROI for the face bounding box and append to frame_buffers
                    x, y, w, h = map(int, new_bbox)
                    roi = frame[y : y + h, x : x + w].copy()  # Extract ROI
                    frame_buffers[label].append(roi)

        current_trackers = next_trackers
        print("current trackers: ", set(label for label, _ in current_trackers))

        draw_labels(frame, current_trackers, frame_buffers)
        clip_counter = remove_old_trackers(
            trackers,
            frame_buffers,
            current_trackers,
            frame_rate,
            frame.shape[1],
            frame.shape[0],
            output_dir,
            clip_counter,
            clip_details,
            json_path,
        )

        cv2.imshow("Frame with Faces", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# Main function
def main():
    app = load_model()
    movie_name = "Inception"  # Replace with desired movie name
    initialize_embeddings_from_movie(movie_name, app)
    output_dir = "output_clips"
    json_path = os.path.join(output_dir, "clip_details.json")
    ensure_output_dir(output_dir)
    video_path = "inception.mp4"
    process_video(video_path, app, output_dir, json_path)


if __name__ == "__main__":
    main()
