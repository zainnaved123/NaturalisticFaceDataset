import cv2
import insightface
import numpy as np
import os


def extract_faces_from_video(video_path, output_base_folder, confidence_threshold=0.5, box_padding=50, clip_duration=10):
    # Load face detection model from InsightFace
    detector = insightface.app.FaceAnalysis()
    detector.prepare(ctx_id=0)

    # Create the output folder structure for faces-only, larger box, and full-frame clips
    output_folders = {
        "faces_only": os.path.join(output_base_folder, "faces_only"),
        "hair_and_shoulders": os.path.join(output_base_folder, "hair_and_shoulders"),
        "full_frame": os.path.join(output_base_folder, "full_frame")
    }
    for folder in output_folders.values():
        os.makedirs(folder, exist_ok=True)

    video_name = os.path.splitext(os.path.basename(video_path))[0]

    # Open video capture
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    clip_frame_count = int(fps * clip_duration)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    success, frame = cap.read()
    frame_idx = 0

    while success:
        # Prepare video writers for each type of clip
        out_writers = {
            "faces_only": cv2.VideoWriter(
                os.path.join(output_folders["faces_only"], f"{video_name}_clip{frame_idx}.mp4"),
                cv2.VideoWriter_fourcc(*"H264"),
                fps,
                (frame_width, frame_height)
            ),
            "hair_and_shoulders": cv2.VideoWriter(
                os.path.join(output_folders["hair_and_shoulders"], f"{video_name}_clip{frame_idx}.mp4"),
                cv2.VideoWriter_fourcc(*"H264"),
                fps,
                (frame_width, frame_height)
            ),
            "full_frame": cv2.VideoWriter(
                os.path.join(output_folders["full_frame"], f"{video_name}_clip{frame_idx}.mp4"),
                cv2.VideoWriter_fourcc(*"H264"),
                fps,
                (frame_width, frame_height)
            )
        }

        for frame_count in range(clip_frame_count):
            if not success:
                break

            # Detect faces in the frame
            faces = detector.get(frame)

            for face in faces:
                if face['det_score'] < confidence_threshold:
                    continue

                # Extract bounding box
                bbox = face['bbox'].astype(int)
                x1, y1, x2, y2 = bbox

                # Faces-only crop
                face_crop = frame[max(0, y1):min(y2, frame_height), max(0, x1):min(x2, frame_width)]

                # Hair-and-shoulders crop
                padding = int(box_padding)
                extended_crop = frame[
                    max(0, y1 - padding):min(y2 + padding, frame_height),
                    max(0, x1 - padding):min(x2 + padding, frame_width)
                ]

                # Full-frame (no cropping, just write the frame)
                full_frame = frame.copy()

                # Center crops within the original dimensions
                def center_crop(crop):
                    if crop.size > 0:
                        h, w, _ = crop.shape
                        canvas = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
                        y_offset = (frame_height - h) // 2
                        x_offset = (frame_width - w) // 2
                        canvas[y_offset:y_offset + h, x_offset:x_offset + w] = crop
                        return canvas
                    else:
                        return np.zeros((frame_height, frame_width, 3), dtype=np.uint8)

                centered_face_crop = center_crop(face_crop)
                centered_extended_crop = center_crop(extended_crop)

                # Write each frame to the respective video writer
                out_writers["faces_only"].write(centered_face_crop)
                out_writers["hair_and_shoulders"].write(centered_extended_crop)
                out_writers["full_frame"].write(full_frame)

            # Read the next frame
            success, frame = cap.read()

        # Release all video writers after each clip
        for writer in out_writers.values():
            writer.release()

        frame_idx += 1

    cap.release()


# Example usage
video_path = "test3.mp4"
output_base_folder = "outputClips"

extract_faces_from_video(video_path, output_base_folder)