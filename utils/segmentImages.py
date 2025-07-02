import os
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
from ultralytics import YOLO
from concurrent.futures import ThreadPoolExecutor
from shutil import rmtree
from collections import Counter


def segment_images_for_photogrammetry(input_folder, output_folder_segmented=None, output_folder_mask=None,
                                      model_path="models/yolo11n-seg.pt", confidence=0.3, max_workers=4,
                                      min_area_ratio=0.08, use_adaptive_confidence=True,
                                      prefer_centered_objects=True):
    """
    Segmenta imágenes para fotogrametría con detección mejorada del objeto principal

    Args:
        input_folder: Carpeta con imágenes de entrada
        output_folder_segmented: Carpeta para imágenes segmentadas
        output_folder_mask: Carpeta para máscaras
        model_path: Ruta al modelo YOLO
        confidence: Umbral de confianza base
        max_workers: Número de hilos
        min_area_ratio: Área mínima del objeto como ratio de la imagen total
        use_adaptive_confidence: Ajustar confianza automáticamente si no hay detecciones
        prefer_centered_objects: Dar preferencia a objetos más centrados
    """
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

    def is_likely_background_mask(mask_binary, original_shape, threshold_edge_ratio=0.7):
        """
        Detecta si una máscara probablemente representa el fondo en lugar del objeto
        """
        height, width = original_shape[:2]

        # 1. Verificar si la máscara toca mucho los bordes de la imagen
        edge_pixels = 0
        edge_pixels += np.sum(mask_binary[0, :])  # Borde superior
        edge_pixels += np.sum(mask_binary[-1, :])  # Borde inferior
        edge_pixels += np.sum(mask_binary[:, 0])  # Borde izquierdo
        edge_pixels += np.sum(mask_binary[:, -1])  # Borde derecho

        total_edge_pixels = 2 * (height + width)
        edge_ratio = edge_pixels / total_edge_pixels

        # 2. Verificar si la máscara forma un "marco" alrededor de la imagen
        center_h, center_w = height // 2, width // 2
        center_region = mask_binary[center_h//2:center_h +
                                    center_h//2, center_w//2:center_w+center_w//2]
        center_filled_ratio = np.sum(center_region) / center_region.size

        # 3. Verificar si ocupa demasiado de la imagen (típico del fondo)
        total_ratio = np.sum(mask_binary) / (height * width)

        # Es probablemente fondo si:
        # - Toca mucho los bordes Y tiene poco relleno en el centro Y ocupa mucho de la imagen
        is_background = (edge_ratio > threshold_edge_ratio and
                         center_filled_ratio < 0.3 and
                         total_ratio > 0.6)

        return is_background, {
            'edge_ratio': edge_ratio,
            'center_filled_ratio': center_filled_ratio,
            'total_ratio': total_ratio
        }

    def calculate_object_importance(mask_binary, confidence, original_shape, box=None, prefer_centered=True):
        """
        Calcula un score de importancia para el objeto detectado, evitando fondos
        """
        total_pixels = original_shape[0] * original_shape[1]
        area = np.sum(mask_binary)
        area_ratio = area / total_pixels

        # Verificar si es probablemente el fondo
        is_background, bg_info = is_likely_background_mask(
            mask_binary, original_shape)
        if is_background:
            return 0.0, {'is_background': True, 'bg_info': bg_info}

        # 1. Score por área (objetos medianos son mejores que muy grandes o muy pequeños)
        if area_ratio < 0.1:
            area_score = area_ratio / 0.1  # Penalizar objetos muy pequeños
        elif area_ratio > 0.7:
            # Penalizar objetos que ocupan casi toda la imagen
            area_score = (1.0 - area_ratio) / 0.3
        else:
            area_score = 1.0  # Área óptima

        # 2. Score por centralidad (más importante si prefer_centered=True)
        moments = cv2.moments(mask_binary)
        if moments['m00'] != 0:
            cx = int(moments['m10'] / moments['m00'])
            cy = int(moments['m01'] / moments['m00'])
            center_x, center_y = original_shape[1] // 2, original_shape[0] // 2

            # Distancia normalizada del centro
            max_distance = np.sqrt(center_x**2 + center_y**2)
            distance_from_center = np.sqrt(
                (cx - center_x)**2 + (cy - center_y)**2)
            centrality_score = 1 - (distance_from_center / max_distance)

            # Bonus por estar en el centro si está habilitado
            if prefer_centered and centrality_score > 0.7:
                centrality_score = min(centrality_score * 1.2, 1.0)
        else:
            centrality_score = 0

        # 3. Score por compacidad (objetos compactos vs dispersos)
        contours, _ = cv2.findContours(
            mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            hull = cv2.convexHull(largest_contour)
            hull_area = cv2.contourArea(hull)
            contour_area = cv2.contourArea(largest_contour)

            # Solidez (qué tan sólido es el objeto)
            solidity = contour_area / hull_area if hull_area > 0 else 0

            # Compacidad
            perimeter = cv2.arcLength(largest_contour, True)
            if perimeter > 0:
                compactness = (4 * np.pi * contour_area) / (perimeter ** 2)
                compactness_score = min(compactness * solidity, 1.0)
            else:
                compactness_score = 0
        else:
            compactness_score = 0

        # 4. Score anti-borde (penalizar objetos que tocan mucho los bordes)
        height, width = original_shape[:2]
        border_penalty = 1.0

        # Verificar contacto con bordes
        if (np.sum(mask_binary[0, :]) > width * 0.1 or  # Borde superior
            np.sum(mask_binary[-1, :]) > width * 0.1 or  # Borde inferior
            np.sum(mask_binary[:, 0]) > height * 0.1 or  # Borde izquierdo
                np.sum(mask_binary[:, -1]) > height * 0.1):  # Borde derecho
            border_penalty = 0.7  # Penalizar objetos que tocan mucho los bordes

        # 5. Score por forma
        if box is not None:
            width_box = box[2] - box[0]
            height_box = box[3] - box[1]
            if width_box > 0 and height_box > 0:
                aspect_ratio = min(width_box/height_box, height_box/width_box)
                shape_score = aspect_ratio
            else:
                shape_score = 0.5
        else:
            shape_score = 0.5

        # Score compuesto con pesos ajustados para fotogrametría
        importance_score = (
            confidence * 0.20 +           # Confianza del modelo
            area_score * 0.25 +           # Tamaño apropiado
            centrality_score * 0.30 +     # Centralidad (muy importante)
            compactness_score * 0.15 +    # Compacidad
            shape_score * 0.10            # Forma
        ) * border_penalty                # Penalización por tocar bordes

        return importance_score, {
            'area_ratio': area_ratio,
            'centrality': centrality_score,
            'compactness': compactness_score,
            'shape_score': shape_score,
            'border_penalty': border_penalty,
            'is_background': False
        }

    def get_main_object_mask(results, original_shape, confidence_threshold, min_area_ratio=0.08):
        """
        Identifica y retorna la máscara del objeto principal, evitando fondos
        """
        if results[0].masks is None or len(results[0].masks) == 0:
            return None, None

        candidates = []
        boxes = results[0].boxes

        for i, mask in enumerate(results[0].masks):
            mask_array = mask.data.cpu().numpy()[0]

            # Redimensionar máscara si es necesario
            if mask_array.shape[:2] != (original_shape[0], original_shape[1]):
                mask_array = cv2.resize(
                    mask_array, (original_shape[1], original_shape[0]))

            mask_binary = (mask_array > 0.5).astype(np.uint8)

            # Filtrar por área mínima
            area_ratio = np.sum(mask_binary) / \
                (original_shape[0] * original_shape[1])
            if area_ratio < min_area_ratio:
                continue

            # Obtener información adicional
            confidence = boxes.conf[i].item() if boxes is not None else 0.5
            box = boxes.xyxy[i].cpu().numpy() if boxes is not None else None
            class_id = int(boxes.cls[i].item()) if boxes is not None else 0

            # Calcular score de importancia
            importance_score, metrics = calculate_object_importance(
                mask_binary, confidence, original_shape, box, prefer_centered_objects)

            # Solo agregar si no es fondo y tiene score positivo
            if importance_score > 0:
                candidates.append({
                    'mask': mask_binary,
                    'importance_score': importance_score,
                    'confidence': confidence,
                    'class_id': class_id,
                    'metrics': metrics
                })

        if not candidates:
            return None, None

        # Ordenar por score de importancia y tomar el mejor
        candidates.sort(key=lambda x: x['importance_score'], reverse=True)
        best_candidate = candidates[0]

        return best_candidate['mask'], best_candidate

    def validate_and_fix_mask(mask_binary, original_shape):
        """
        Valida y corrige la máscara final si es necesario
        """
        # Si la máscara ocupa más del 80% de la imagen, probablemente está invertida
        total_pixels = original_shape[0] * original_shape[1]
        filled_ratio = np.sum(mask_binary) / total_pixels

        if filled_ratio > 0.8:
            print("    ⚠️  Máscara sospechosa (>80% filled), verificando...")

            # Verificar si invertir la máscara da mejor resultado
            inverted_mask = 1 - mask_binary
            inverted_ratio = np.sum(inverted_mask) / total_pixels

            # Si la máscara invertida está en un rango más razonable, usarla
            if 0.1 <= inverted_ratio <= 0.6:
                print("    🔄 Invirtiendo máscara automáticamente")
                return inverted_mask

        return mask_binary

    def process_image(img_path):
        try:
            original_image = cv2.imread(img_path)
            if original_image is None:
                print(f"Error: No se pudo cargar la imagen: {img_path}")
                return None, None

            current_confidence = confidence
            mask = None
            best_info = None

            # Intentar con diferentes niveles de confianza si está habilitado
            if use_adaptive_confidence:
                confidence_levels = [confidence, confidence *
                                     0.8, confidence * 0.6, confidence * 0.4]
            else:
                confidence_levels = [confidence]

            for conf_level in confidence_levels:
                results = model(img_path, conf=conf_level)
                mask, best_info = get_main_object_mask(
                    results, original_image.shape, conf_level, min_area_ratio)

                if mask is not None:
                    current_confidence = conf_level
                    break

            if mask is not None:
                # Validar y corregir la máscara si es necesario
                mask = validate_and_fix_mask(mask, original_image.shape)

                # Suavizar la máscara para mejores bordes
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                # Rellenar pequeños huecos en el objeto principal
                kernel_large = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_large)

                segmented_image = np.zeros_like(original_image)
                segmented_image[mask == 1] = original_image[mask == 1]

                base_name = os.path.basename(img_path)
                file_name, file_ext = os.path.splitext(base_name)

                segmented_path = os.path.join(
                    output_folder_segmented, f"seg_{file_name}.jpg")
                mask_path = os.path.join(
                    output_folder_mask, f"mask_{base_name}")

                cv2.imwrite(segmented_path, segmented_image)
                cv2.imwrite(mask_path, mask * 255)

                # Información de debug
                if best_info:
                    metrics = best_info['metrics']
                    area_pct = metrics['area_ratio'] * 100
                    centrality_pct = metrics['centrality'] * 100
                    print(f"✓ {base_name}: Score={best_info['importance_score']:.3f}, "
                          f"Área={area_pct:.1f}%, Centro={centrality_pct:.0f}%, Conf={current_confidence:.2f}")

                return segmented_path, mask_path
            else:
                print(
                    f"✗ No se encontró objeto principal válido en: {os.path.basename(img_path)}")
                return None, None

        except Exception as e:
            print(f"Error al procesar {img_path}: {str(e)}")
            return None, None

    print("Segmentando imágenes...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(
            tqdm(executor.map(process_image, image_paths), total=len(image_paths)))

    segmented_paths = []
    mask_paths = []

    for seg_path, mask_path in results:
        if seg_path is not None and mask_path is not None:
            segmented_paths.append(seg_path)
            mask_paths.append(mask_path)

    success_rate = len(segmented_paths) / len(image_paths) * 100
    print(f"\nSegmentación completada:")
    print(
        f"✓ Procesadas exitosamente: {len(segmented_paths)} de {len(image_paths)} imágenes ({success_rate:.1f}%)")
    print(f"✓ Imágenes segmentadas guardadas en: {output_folder_segmented}")
    print(f"✓ Máscaras guardadas en: {output_folder_mask}")

    return segmented_paths, mask_paths


def preprocess_image_for_detection(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    enhanced = cv2.filter2D(enhanced, -1, kernel)

    return enhanced


def calculate_object_centrality(bbox, image_shape):
    h, w = image_shape[:2]
    center_x, center_y = w // 2, h // 2

    x1, y1, x2, y2 = bbox
    obj_center_x = (x1 + x2) / 2
    obj_center_y = (y1 + y2) / 2

    distance = np.sqrt((obj_center_x - center_x)**2 +
                       (obj_center_y - center_y)**2)
    max_distance = np.sqrt(center_x**2 + center_y**2)

    centrality = 1 - (distance / max_distance)
    return centrality


def calculate_object_compactness(mask):
    contours, _ = cv2.findContours(mask.astype(
        np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0

    main_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(main_contour)
    perimeter = cv2.arcLength(main_contour, True)

    if perimeter == 0:
        return 0

    compactness = 4 * np.pi * area / (perimeter * perimeter)
    return compactness


def filter_background_objects(detections, image_shape):
    filtered = []
    h, w = image_shape[:2]

    for detection in detections:
        bbox = detection['bbox']
        x1, y1, x2, y2 = bbox

        obj_w = x2 - x1
        obj_h = y2 - y1

        is_edge_object = (x1 < w * 0.02 and y1 < h * 0.02 and
                          x2 > w * 0.98 and y2 > h * 0.98)

        aspect_ratio = obj_w / obj_h if obj_h > 0 else 0
        is_background_like = (aspect_ratio > 3 or aspect_ratio < 0.3)

        area_ratio = (obj_w * obj_h) / (w * h)
        is_too_large = area_ratio > 0.85

        if not (is_edge_object or is_background_like or is_too_large):
            filtered.append(detection)

    return filtered


def select_best_object(detections, image_shape):
    if not detections:
        return None

    if len(detections) == 1:
        return detections[0]

    scores = []
    for detection in detections:
        confidence = detection['confidence']
        centrality = calculate_object_centrality(
            detection['bbox'], image_shape)
        compactness = calculate_object_compactness(detection['mask'])

        area_ratio = detection['area_ratio']
        area_score = 1 - abs(area_ratio - 0.3) / 0.7 if area_ratio <= 1 else 0

        final_score = (confidence * 0.3 +
                       centrality * 0.35 +
                       compactness * 0.2 +
                       area_score * 0.15)

        scores.append(final_score)

    best_idx = np.argmax(scores)
    return detections[best_idx]


def segment_single_object_adaptive(image_path, model, confidence_levels=[0.3, 0.2, 0.15, 0.1, 0.08]):
    original_image = cv2.imread(image_path)
    if original_image is None:
        return None, None

    enhanced_image = preprocess_image_for_detection(original_image)
    h, w = original_image.shape[:2]

    for confidence in confidence_levels:
        results = model(enhanced_image, conf=confidence, iou=0.7, max_det=100)

        if not results or not results[0].masks:
            continue

        detections = []
        masks = results[0].masks.data.cpu().numpy()
        boxes = results[0].boxes.xyxy.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()

        for i, (mask, box, conf) in enumerate(zip(masks, boxes, confidences)):
            mask_resized = cv2.resize(mask, (w, h))
            mask_area = np.sum(mask_resized > 0.5)
            area_ratio = mask_area / (w * h)

            if area_ratio < 0.005 or area_ratio > 0.85:
                continue

            detections.append({
                'mask': mask_resized,
                'bbox': box,
                'confidence': conf,
                'area_ratio': area_ratio
            })

        filtered_detections = filter_background_objects(
            detections, original_image.shape)

        if filtered_detections:
            best_detection = select_best_object(
                filtered_detections, original_image.shape)
            if best_detection:
                mask_binary = (best_detection['mask'] > 0.5).astype(
                    np.uint8) * 255
                return original_image, mask_binary

    return None, None


def segment_images_for_photogrammetry_improved(input_folder, output_folder_segmented, output_folder_mask, model_path):
    import os
    import shutil
    from tqdm import tqdm

    if os.path.exists(output_folder_segmented):
        shutil.rmtree(output_folder_segmented)
    if os.path.exists(output_folder_mask):
        shutil.rmtree(output_folder_mask)

    os.makedirs(output_folder_segmented, exist_ok=True)
    os.makedirs(output_folder_mask, exist_ok=True)

    model = YOLO(model_path)

    image_files = [f for f in os.listdir(input_folder)
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    segmented_paths = []
    mask_paths = []

    for image_file in tqdm(image_files, desc="Segmentando objetos"):
        image_path = os.path.join(input_folder, image_file)

        segmented_image, mask = segment_single_object_adaptive(
            image_path, model)

        if segmented_image is not None and mask is not None:
            mask_3d = cv2.merge([mask, mask, mask])
            segmented_result = cv2.bitwise_and(segmented_image, mask_3d)

            base_name = os.path.splitext(image_file)[0]

            segmented_output_path = os.path.join(
                output_folder_segmented, f"{base_name}_seg.jpg")
            mask_output_path = os.path.join(
                output_folder_mask, f"{base_name}_mask.jpg")

            cv2.imwrite(segmented_output_path, segmented_result)
            cv2.imwrite(mask_output_path, mask)

            segmented_paths.append(segmented_output_path)
            mask_paths.append(mask_output_path)

    return segmented_paths, mask_paths


def modify_upload_endpoint_segmentation():
    return '''
    if segment_objects:
        try:
            segmented_paths, mask_paths = segment_images_for_photogrammetry_improved(
                input_folder="/data/images",
                output_folder_segmented="/data/images_segmented", 
                output_folder_mask="/data/images_masks",
                model_path="/app/models/yolo11l-seg.pt"
            )

            if segmented_paths:
                shutil.rmtree("/data/images")
                os.rename("/data/images_segmented", "/data/images")
                if os.path.exists("/data/images_masks"):
                    shutil.rmtree("/data/images_masks")

                segmentation_info = {
                    "segmented": True,
                    "segmented_images": len(segmented_paths),
                    "original_images": len(copied_images)
                }
            else:
                segmentation_info = {
                    "segmented": False,
                    "reason": "No se encontraron objetos válidos para segmentar",
                    "fallback_to_original": True
                }
        except Exception as seg_error:
            segmentation_info = {
                "segmented": False,
                "error": str(seg_error),
                "fallback_to_original": True
            }
    '''
