import cv2
import os
import numpy as np


def extract_frames_from_video(video_path, output_folder="images", num_frames=25):
    """
    Extrae un número específico de frames uniformemente distribuidos de un video.

    Args:
        video_path (str): Ruta al archivo de video.
        output_folder (str): Carpeta donde guardar los frames extraídos.
        num_frames (int): Número de frames a extraer (por defecto 25).

    Returns:
        list: Lista de rutas a los frames extraídos.
    """
    # Crear carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta '{output_folder}' creada.")

    # Abrir el video
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise ValueError(f"No se pudo abrir el video: {video_path}")

    # Obtener información del video
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0

    print(f"Video: {os.path.basename(video_path)}")
    print(f"Duración: {duration:.2f} segundos")
    print(f"Total de frames: {total_frames}")
    print(f"FPS: {fps}")

    if total_frames <= 0:
        raise ValueError("No se detectaron frames en el video")

    # Calcular los índices de frames a extraer (distribución uniforme)
    if num_frames >= total_frames:
        # Si hay menos frames que los solicitados, tomar todos
        frame_indices = np.arange(total_frames)
        print(
            f"El video tiene menos frames ({total_frames}) que los solicitados ({num_frames}). Extrayendo todos los frames disponibles.")
    else:
        # Distribuir uniformemente
        frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

    extracted_frames = []

    # Extraer los frames seleccionados
    print(f"Extrayendo {len(frame_indices)} frames...")

    for i, frame_idx in enumerate(frame_indices):
        # Establecer la posición del video al frame deseado
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

        # Leer el frame
        success, frame = video.read()
        if not success:
            print(f"No se pudo leer el frame {frame_idx}")
            continue

        # Guardar el frame
        timestamp = frame_idx / fps if fps > 0 else 0
        output_path = os.path.join(
            output_folder, f"frame_{i+1:03d}_{timestamp:.2f}s.jpg")

        cv2.imwrite(output_path, frame)
        extracted_frames.append(output_path)

        print(
            f"Extraído frame {i+1}/{len(frame_indices)} - Posición: {timestamp:.2f}s")

    # Liberar recursos
    video.release()

    print(
        f"Proceso completado. Se extrajeron {len(extracted_frames)} frames en '{output_folder}'")
    return extracted_frames
