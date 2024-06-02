import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, VideoClip


def rotate_frame(frame, angle):
    (h, w) = frame.shape[:2]
    center = (w / 2, h / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(frame, matrix, (w, h))


def flip_frame(frame, flip_code):
    return cv2.flip(frame, flip_code)


def adjust_brightness_contrast(frame, brightness=0, contrast=0):
    frame = cv2.convertScaleAbs(frame, alpha=1 + contrast / 127.0, beta=brightness)
    return frame


def add_noise(frame, mean=0, var=10):
    sigma = var**0.5
    gauss = np.random.normal(mean, sigma, frame.shape).astype("uint8")
    noisy_frame = cv2.add(frame, gauss)
    return noisy_frame


def process_clip(input_path, output_dir, augmentation, param):
    clip = VideoFileClip(input_path)
    fps = clip.fps
    duration = clip.duration
    width, height = clip.size

    def make_frame(t):
        frame = clip.get_frame(t)
        if augmentation == "rotate":
            frame = rotate_frame(frame, param)
        elif augmentation == "flip":
            frame = flip_frame(frame, param)
        elif augmentation == "brightness_contrast":
            brightness, contrast = param
            frame = adjust_brightness_contrast(frame, brightness, contrast)
        elif augmentation == "noise":
            frame = add_noise(frame, param)
        return frame

    augmented_clip = VideoClip(make_frame, duration=duration)
    augmented_clip = augmented_clip.set_fps(fps)
    augmented_clip_path = os.path.join(
        output_dir,
        f"{os.path.splitext(os.path.basename(input_path))[0]}_{augmentation}.mp4",
    )
    augmented_clip.write_videofile(augmented_clip_path, codec="libx264")


def main():
    input_dir = "output_clips"
    output_dir = "augmented_clips"
    os.makedirs(output_dir, exist_ok=True)
    augmentations = ["rotate", "flip", "brightness_contrast", "noise"]

    for filename in os.listdir(input_dir):
        if filename.endswith(".mp4"):
            input_path = os.path.join(input_dir, filename)
            for augmentation in augmentations:
                if augmentation == "rotate":
                    param = np.random.choice([90, 180, 270])
                elif augmentation == "flip":
                    param = np.random.choice([-1, 0, 1])
                elif augmentation == "brightness_contrast":
                    param = (np.random.randint(-50, 50), np.random.randint(-30, 30))
                elif augmentation == "noise":
                    param = 10  # Fixed noise variance
                process_clip(input_path, output_dir, augmentation, param)
            break


if __name__ == "__main__":
    main()
