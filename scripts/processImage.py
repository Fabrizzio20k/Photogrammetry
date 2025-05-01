import os
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from shutil import rmtree


def preprocess_images_for_photogrammetry(input_folder, output_folder=None, min_resolution=2000,
                                         blur_threshold=100, contrast_enhancement=1.2,
                                         brightness_adjustment=5, max_images=None):
    """
    Preprocesa imágenes para optimizarlas para fotogrametría.

    Args:
        input_folder (str): Ruta a la carpeta con imágenes originales.
        output_folder (str, optional): Carpeta donde guardar imágenes procesadas. Si es None,
                                      se crea una subcarpeta 'processed' dentro de input_folder.
        min_resolution (int): Resolución mínima (lado más pequeño) en píxeles.
        blur_threshold (float): Umbral para detectar imágenes borrosas (menor = más estricto).
        contrast_enhancement (float): Factor de mejora de contraste.
        brightness_adjustment (int): Ajuste de brillo (-255 a 255).
        max_images (int, optional): Máximo número de imágenes a procesar/retener.

    Returns:
        list: Lista de rutas a las imágenes procesadas.
    """
    if output_folder is None:
        output_folder = os.path.join(input_folder, "processed")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
        rmtree(output_folder)
        os.makedirs(output_folder)

    # Obtener todas las imágenes de la carpeta (corregido para evitar duplicados)
    valid_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    image_paths = []

    # Usar set para evitar duplicados
    unique_files = set()

    for ext in valid_extensions:
        for file_path in Path(input_folder).glob(f'*{ext.lower()}'):
            if str(file_path) not in unique_files:
                unique_files.add(str(file_path))
                image_paths.append(file_path)

        # También buscar extensiones en mayúscula
        for file_path in Path(input_folder).glob(f'*{ext.upper()}'):
            if str(file_path) not in unique_files:
                unique_files.add(str(file_path))
                image_paths.append(file_path)

    print(
        f"Encontradas {len(image_paths)} imágenes únicas en la carpeta de entrada.")

    # Resultados del procesamiento
    processed_images = []
    image_scores = []  # Para almacenar puntuaciones de calidad

    def process_image(img_path):
        try:
            # Leer imagen
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"No se pudo leer la imagen: {img_path}")
                return None, -1

            height, width = img.shape[:2]
            min_side = min(height, width)
            if min_side < min_resolution:
                return None, -1

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            if blur_score < blur_threshold:
                return None, -1

            clahe = cv2.createCLAHE(
                clipLimit=contrast_enhancement, tileGridSize=(8, 8))
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            lab_planes = list(cv2.split(lab))
            lab_planes[0] = clahe.apply(lab_planes[0])
            lab = cv2.merge(lab_planes)
            img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

            if brightness_adjustment != 0:
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                v = cv2.add(v, brightness_adjustment)
                v = np.clip(v, 0, 255)
                hsv = cv2.merge([h, s, v])
                img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

            contrast_score = np.std(gray)
            entropy = -np.sum(np.histogram(gray, bins=256, range=[0, 256])[0]/gray.size *
                              np.log2(np.histogram(gray, bins=256, range=[0, 256])[0]/gray.size + 1e-10))

            quality_score = blur_score * 0.5 + contrast_score * 0.3 + entropy * 0.2

            base_name = os.path.basename(img_path)
            output_path = os.path.join(output_folder, f"proc_{base_name}")
            cv2.imwrite(output_path, img)

            if not os.path.exists(output_path):
                print(
                    f"¡Advertencia! No se pudo guardar la imagen: {output_path}")
                return None, -1

            return output_path, quality_score

        except Exception as e:
            print(f"Error al procesar {img_path}: {str(e)}")
            return None, -1

    print("Procesando imágenes...")
    with ThreadPoolExecutor() as executor:
        results = list(
            tqdm(executor.map(process_image, image_paths), total=len(image_paths)))

    valid_results = [(path, score)
                     for path, score in results if path is not None]

    print(f"Imágenes válidas después del procesamiento: {len(valid_results)}")

    valid_results.sort(key=lambda x: x[1], reverse=True)

    output_filenames = [os.path.basename(path) for path, _ in valid_results]
    duplicate_filenames = set([name for name in output_filenames
                              if output_filenames.count(name) > 1])

    if duplicate_filenames:
        print(
            f"¡ADVERTENCIA! Se detectaron nombres de archivo duplicados que podrían causar sobrescrituras: {duplicate_filenames}")

    if max_images and len(valid_results) > max_images:
        print(
            f"Limitando a las mejores {max_images} imágenes de {len(valid_results)} válidas")

        removed_images = [path for path, _ in valid_results[max_images:]]
        print(f"Se eliminarán {len(removed_images)} imágenes")

        for path, _ in valid_results[max_images:]:
            if os.path.exists(path):
                os.remove(path)
                if os.path.exists(path):
                    print(f"¡Error! No se pudo eliminar: {path}")

        valid_results = valid_results[:max_images]

    processed_paths = [path for path, _ in valid_results]

    actual_files = list(Path(output_folder).glob('*.*'))
    print(f"Imágenes realmente guardadas en disco: {len(actual_files)}")

    if len(actual_files) != len(processed_paths):
        print("¡ADVERTENCIA! El número de archivos en disco no coincide con el número esperado.")
        print(
            f"Esperados: {len(processed_paths)}, En disco: {len(actual_files)}")

    print(
        f"Procesamiento completado. Se obtuvieron {len(processed_paths)} imágenes optimizadas.")

    return processed_paths
