import os
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor


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
    # Crear carpeta de salida si no se especifica
    if output_folder is None:
        output_folder = os.path.join(input_folder, "processed")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Obtener todas las imágenes de la carpeta
    valid_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    image_paths = []

    for ext in valid_extensions:
        image_paths.extend(list(Path(input_folder).glob(f'*{ext}')))
        image_paths.extend(list(Path(input_folder).glob(f'*{ext.upper()}')))

    print(f"Encontradas {len(image_paths)} imágenes en la carpeta de entrada.")

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

            # Verificar resolución
            height, width = img.shape[:2]
            min_side = min(height, width)
            if min_side < min_resolution:
                print(
                    f"Resolución demasiado baja: {img_path} ({width}x{height})")
                return None, -1

            # Detectar borrosidad usando la varianza del Laplaciano
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            if blur_score < blur_threshold:
                print(
                    f"Imagen demasiado borrosa: {img_path} (score: {blur_score:.2f})")
                return None, -1

            # Mejorar contraste usando CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(
                clipLimit=contrast_enhancement, tileGridSize=(8, 8))
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            lab_planes = list(cv2.split(lab))
            lab_planes[0] = clahe.apply(lab_planes[0])
            lab = cv2.merge(lab_planes)
            img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

            # Ajustar brillo
            if brightness_adjustment != 0:
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                v = cv2.add(v, brightness_adjustment)
                v = np.clip(v, 0, 255)
                hsv = cv2.merge([h, s, v])
                img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

            # Calcular una puntuación de calidad combinada
            # basada en nitidez, contraste y entropía para selección posterior
            contrast_score = np.std(gray)
            entropy = -np.sum(np.histogram(gray, bins=256, range=[0, 256])[0]/gray.size *
                              np.log2(np.histogram(gray, bins=256, range=[0, 256])[0]/gray.size + 1e-10))

            quality_score = blur_score * 0.5 + contrast_score * 0.3 + entropy * 0.2

            base_name = os.path.basename(img_path)
            output_path = os.path.join(output_folder, f"proc_{base_name}")
            cv2.imwrite(output_path, img)

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

    valid_results.sort(key=lambda x: x[1], reverse=True)

    if max_images and len(valid_results) > max_images:
        print(
            f"Limitando a las mejores {max_images} imágenes de {len(valid_results)} válidas")

        for path, _ in valid_results[max_images:]:
            if os.path.exists(path):
                os.remove(path)
        valid_results = valid_results[:max_images]

    processed_paths = [path for path, _ in valid_results]
    print(
        f"Procesamiento completado. Se obtuvieron {len(processed_paths)} imágenes optimizadas.")

    return processed_paths
