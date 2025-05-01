import os
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
from ultralytics import YOLO
from concurrent.futures import ThreadPoolExecutor
from shutil import rmtree


def segment_images_for_photogrammetry(input_folder, output_folder_segmented=None, output_folder_mask=None, model_path="models/yolo11n-seg.pt",
                                      confidence=0.5, max_workers=4):
    if output_folder_segmented is None:
        output_folder_segmented = os.path.join(input_folder, "segmented")

    if output_folder_mask is None:
        output_folder_mask = os.path.join(input_folder, "masks")

    for folder in [output_folder_segmented, output_folder_mask]:
        if not os.path.exists(folder):
            os.makedirs(folder)
        else:
            rmtree(folder)
            os.makedirs(folder)

    model = YOLO(model_path)

    valid_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    image_paths = []

    for ext in valid_extensions:
        image_paths.extend(list(Path(input_folder).glob(f'*{ext.lower()}')))
        image_paths.extend(list(Path(input_folder).glob(f'*{ext.upper()}')))

    image_paths = list(set([str(path) for path in image_paths]))
    print(f"Encontradas {len(image_paths)} imágenes en la carpeta de entrada.")

    def process_image(img_path):
        try:
            original_image = cv2.imread(img_path)
            if original_image is None:
                print(f"Error: No se pudo cargar la imagen: {img_path}")
                return None, None

            results = model(img_path, conf=confidence)

            if results[0].masks is not None and len(results[0].masks) > 0:
                mask = results[0].masks[0].data.cpu().numpy()[0]

                if mask.shape[:2] != (original_image.shape[0], original_image.shape[1]):
                    mask = cv2.resize(
                        mask, (original_image.shape[1], original_image.shape[0]))

                mask = (mask > 0.5).astype(np.uint8)

                background = np.ones_like(original_image) * 255

                segmented_image = np.copy(original_image)
                segmented_image[mask == 0] = background[mask == 0]

                base_name = os.path.basename(img_path)
                segmented_path = os.path.join(
                    output_folder_segmented, f"seg_{base_name}")
                mask_path = os.path.join(
                    output_folder_mask, f"mask_{base_name}")

                cv2.imwrite(segmented_path, segmented_image)
                cv2.imwrite(mask_path, mask * 255)

                return segmented_path, mask_path
            else:
                print(f"No se encontraron objetos segmentables en: {img_path}")
                return None, None

        except Exception as e:
            print(f"Error al procesar {img_path}: {str(e)}")
            return None, None

    print("Segmentando imágenes...")
    processed_results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(
            tqdm(executor.map(process_image, image_paths), total=len(image_paths)))

    segmented_paths = []
    mask_paths = []

    for seg_path, mask_path in results:
        if seg_path is not None and mask_path is not None:
            segmented_paths.append(seg_path)
            mask_paths.append(mask_path)

    print(
        f"Segmentación completada. Se procesaron {len(segmented_paths)} de {len(image_paths)} imágenes.")
    print(f"Imágenes segmentadas guardadas en: {output_folder_segmented}")
    print(f"Máscaras guardadas en: {output_folder_mask}")

    return segmented_paths, mask_paths
