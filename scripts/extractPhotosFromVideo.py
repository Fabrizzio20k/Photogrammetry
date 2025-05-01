import cv2
import os
import numpy as np
from shutil import rmtree
from tqdm import tqdm


def extract_frames_from_video(video_path, output_folder="images", num_frames=25, quality=95):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
        rmtree(output_folder)
        os.makedirs(output_folder)

    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise ValueError(f"No se pudo abrir el video: {video_path}")

    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0

    print(f"Video: {os.path.basename(video_path)}")
    print(f"Dimensiones originales: {width}x{height} píxeles")
    print(f"Duración: {duration:.2f} segundos")
    print(f"Total de frames: {total_frames}")
    print(f"FPS: {fps}")

    is_vertical = True
    print(f"Forzando orientación vertical para el video")

    if total_frames <= 0:
        raise ValueError("No se detectaron frames en el video")

    if num_frames >= total_frames:
        frame_indices = np.arange(total_frames)
        print(f"El video tiene menos frames ({total_frames}) que los solicitados ({num_frames}). "
              f"Extrayendo todos los frames disponibles.")
    else:
        frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

    extracted_frames = []

    print(f"Extrayendo {len(frame_indices)} frames...")

    for i, frame_idx in enumerate(tqdm(frame_indices, desc="Extrayendo frames")):
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

        success, frame = video.read()
        if not success:
            print(f"No se pudo leer el frame {frame_idx}")
            continue

        if frame.shape[1] > frame.shape[0]:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        timestamp = frame_idx / fps if fps > 0 else 0
        output_path = os.path.join(
            output_folder, f"frame_{i+1:03d}_{timestamp:.2f}s.jpg")

        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        cv2.imwrite(output_path, frame, encode_params)

        extracted_frames.append(output_path)

    video.release()

    print(
        f"Proceso completado. Se extrajeron {len(extracted_frames)} frames en '{output_folder}'")
