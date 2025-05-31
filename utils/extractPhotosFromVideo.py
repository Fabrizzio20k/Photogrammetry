import cv2
import os
import numpy as np
from shutil import rmtree
from tqdm import tqdm


def calculate_frame_sharpness(frame):
    """
    Calcula la nitidez de un frame usando la varianza del Laplaciano
    Valores más altos = más nítido
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var


def calculate_frame_quality_score(frame):
    """
    Calcula un score de calidad general del frame considerando múltiples factores
    """
    # 1. Nitidez (varianza del Laplaciano)
    sharpness = calculate_frame_sharpness(frame)

    # 2. Contraste (desviación estándar de los píxeles)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    contrast = np.std(gray)

    # 3. Exposición (evitar sobre/sub exposición)
    # Penalizar si hay demasiados píxeles muy oscuros o muy claros
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    total_pixels = frame.shape[0] * frame.shape[1]

    # Porcentaje de píxeles muy oscuros (0-20) y muy claros (235-255)
    dark_pixels = np.sum(hist[0:21]) / total_pixels
    bright_pixels = np.sum(hist[235:256]) / total_pixels

    # Score de exposición (mejor cuando hay pocos píxeles en extremos)
    exposure_score = max(0, 1 - (dark_pixels + bright_pixels) * 2)

    # 4. Información/Entropía (más información = mejor)
    hist_norm = hist.flatten() / total_pixels
    hist_norm = hist_norm[hist_norm > 0]  # Evitar log(0)
    entropy = -np.sum(hist_norm * np.log2(hist_norm))
    entropy_score = min(entropy / 8.0, 1.0)  # Normalizar a 0-1

    # Score compuesto
    quality_score = (
        min(sharpness / 500, 1.0) * 0.4 +      # Nitidez (normalizada)
        min(contrast / 60, 1.0) * 0.3 +        # Contraste (normalizada)
        exposure_score * 0.2 +                  # Exposición
        entropy_score * 0.1                     # Información
    )

    return quality_score, {
        'sharpness': sharpness,
        'contrast': contrast,
        'exposure_score': exposure_score,
        'entropy_score': entropy_score
    }


def calculate_frame_similarity(frame1, frame2):
    """
    Calcula la similitud entre dos frames usando histogramas
    Retorna valor entre 0 (muy diferentes) y 1 (idénticos)
    """
    # Convertir a HSV para mejor comparación
    hsv1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)

    # Calcular histogramas
    hist1 = cv2.calcHist([hsv1], [0, 1, 2], None, [
                         50, 60, 60], [0, 180, 0, 256, 0, 256])
    hist2 = cv2.calcHist([hsv2], [0, 1, 2], None, [
                         50, 60, 60], [0, 180, 0, 256, 0, 256])

    # Normalizar histogramas
    cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

    # Calcular correlación
    correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return correlation


def calculate_optimal_frame_count(duration_seconds, fps, min_frames=10, max_frames=200):
    """
    Calcula el número óptimo de frames basado en la duración del video
    """
    # Reglas heurísticas para fotogrametría
    if duration_seconds <= 5:
        optimal = max(min_frames, min(duration_seconds * 3, max_frames))
    elif duration_seconds <= 15:
        optimal = max(min_frames, min(duration_seconds * 2, max_frames))
    elif duration_seconds <= 30:
        optimal = max(min_frames, min(duration_seconds * 1.5, max_frames))
    elif duration_seconds <= 60:
        optimal = max(min_frames, min(duration_seconds * 1, max_frames))
    else:
        optimal = max(min_frames, min(duration_seconds * 0.8, max_frames))

    return int(optimal)


def extract_frames_from_video_smart(video_path, output_folder="images", num_frames=None,
                                    quality=95, min_sharpness=None, max_similarity=0.85,
                                    quality_threshold=None, force_vertical=True,
                                    analysis_sample=0.1, debug_mode=False):
    """
    Extrae frames de un video con filtrado inteligente de calidad

    Args:
        video_path: Ruta del video
        output_folder: Carpeta de salida
        num_frames: Número de frames objetivo (None para cálculo automático)
        quality: Calidad JPEG (1-100)
        min_sharpness: Nitidez mínima requerida (None para cálculo automático)
        max_similarity: Similitud máxima entre frames consecutivos (0-1)
        quality_threshold: Umbral mínimo de calidad general (None para cálculo automático)
        force_vertical: Forzar orientación vertical
        analysis_sample: Fracción del video a analizar para estadísticas (0.1 = 10%)
        debug_mode: Mostrar información detallada de debug
    """
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

    print(f"🎥 Video: {os.path.basename(video_path)}")
    print(f"📐 Dimensiones: {width}x{height} píxeles")
    print(f"⏱️  Duración: {duration:.2f} segundos")
    print(f"🎞️  Total frames: {total_frames}, FPS: {fps:.1f}")

    if total_frames <= 0:
        raise ValueError("No se detectaron frames en el video")

    # Calcular número óptimo de frames si no se especifica
    if num_frames is None:
        num_frames = calculate_optimal_frame_count(duration, fps)
        print(f"🧮 Frames objetivo calculado automáticamente: {num_frames}")
    else:
        print(f"🎯 Frames objetivo especificado: {num_frames}")

    # FASE 1: Análisis de calidad en una muestra del video
    print("\n📊 Fase 1: Analizando calidad del video...")

    sample_size = max(10, int(total_frames * analysis_sample))
    sample_indices = np.linspace(0, total_frames - 1, sample_size, dtype=int)

    sharpness_values = []
    quality_scores = []

    for frame_idx in tqdm(sample_indices, desc="Analizando muestra"):
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = video.read()

        if success:
            if force_vertical and frame.shape[1] > frame.shape[0]:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

            sharpness = calculate_frame_sharpness(frame)
            quality_score, _ = calculate_frame_quality_score(frame)

            sharpness_values.append(sharpness)
            quality_scores.append(quality_score)

    if not sharpness_values:
        raise ValueError("No se pudieron analizar frames del video")

    # Estadísticas de calidad
    avg_sharpness = np.mean(sharpness_values)
    std_sharpness = np.std(sharpness_values)
    min_sharpness_found = np.min(sharpness_values)
    max_sharpness_found = np.max(sharpness_values)
    avg_quality = np.mean(quality_scores)
    std_quality = np.std(quality_scores)
    min_quality_found = np.min(quality_scores)
    max_quality_found = np.max(quality_scores)

    if debug_mode:
        print(f"   🔍 Debug - Estadísticas de nitidez:")
        print(
            f"      Min: {min_sharpness_found:.1f}, Max: {max_sharpness_found:.1f}")
        print(f"      Promedio: {avg_sharpness:.1f} ± {std_sharpness:.1f}")
        print(f"   🔍 Debug - Estadísticas de calidad:")
        print(
            f"      Min: {min_quality_found:.3f}, Max: {max_quality_found:.3f}")
        print(f"      Promedio: {avg_quality:.3f} ± {std_quality:.3f}")

    # Ajustar umbrales basados en las características del video (más permisivos)
    if min_sharpness is None:
        # Usar percentil 25 en lugar de promedio - desviación
        adaptive_min_sharpness = np.percentile(sharpness_values, 25)
    else:
        adaptive_min_sharpness = min_sharpness

    if quality_threshold is None:
        # Usar percentil 25 para ser más permisivo
        adaptive_quality_threshold = np.percentile(quality_scores, 25)
    else:
        adaptive_quality_threshold = quality_threshold

    print(
        f"   📈 Nitidez - Min encontrada: {min_sharpness_found:.1f}, Promedio: {avg_sharpness:.1f}")
    print(f"   🎯 Usando umbral de nitidez: {adaptive_min_sharpness:.1f}")
    print(
        f"   🏆 Calidad - Min encontrada: {min_quality_found:.3f}, Promedio: {avg_quality:.3f}")
    print(f"   🎯 Usando umbral de calidad: {adaptive_quality_threshold:.3f}")

    # FASE 2: Extracción inteligente de frames
    print(f"\n🎯 Fase 2: Extrayendo frames con filtrado de calidad...")

    # Calcular frames candidatos (más de los necesarios para filtrar)
    candidate_multiplier = 3  # Extraer 3x más candidatos para filtrar
    candidate_frames = min(num_frames * candidate_multiplier, total_frames)
    candidate_indices = np.linspace(
        0, total_frames - 1, candidate_frames, dtype=int)

    frame_candidates = []

    for i, frame_idx in enumerate(tqdm(candidate_indices, desc="Evaluando candidatos")):
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = video.read()

        if not success:
            continue

        if force_vertical and frame.shape[1] > frame.shape[0]:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        # Calcular métricas de calidad
        sharpness = calculate_frame_sharpness(frame)
        quality_score, quality_metrics = calculate_frame_quality_score(frame)

        # Filtrar por umbrales mínimos
        if sharpness >= adaptive_min_sharpness and quality_score >= adaptive_quality_threshold:
            timestamp = frame_idx / fps if fps > 0 else 0

            frame_candidates.append({
                'frame': frame.copy(),
                'frame_idx': frame_idx,
                'timestamp': timestamp,
                'sharpness': sharpness,
                'quality_score': quality_score,
                'quality_metrics': quality_metrics
            })

    print(f"   ✅ Candidatos de calidad encontrados: {len(frame_candidates)}")

    if len(frame_candidates) == 0:
        print("⚠️  No se encontraron frames de suficiente calidad. Aplicando umbrales de emergencia...")

        # Umbrales de emergencia mucho más permisivos
        emergency_min_sharpness = np.percentile(
            sharpness_values, 10) if len(sharpness_values) > 0 else 10
        emergency_quality_threshold = np.percentile(
            quality_scores, 10) if len(quality_scores) > 0 else 0.1

        print(
            f"   🚨 Umbrales de emergencia - Nitidez: {emergency_min_sharpness:.1f}, Calidad: {emergency_quality_threshold:.3f}")

        for i, frame_idx in enumerate(tqdm(candidate_indices, desc="Re-evaluando con umbrales de emergencia")):
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            success, frame = video.read()

            if not success:
                continue

            if force_vertical and frame.shape[1] > frame.shape[0]:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

            sharpness = calculate_frame_sharpness(frame)
            quality_score, quality_metrics = calculate_frame_quality_score(
                frame)

            if debug_mode and i < 10:  # Solo mostrar los primeros 10 para debug
                print(
                    f"      Frame {i}: Nitidez={sharpness:.1f}, Calidad={quality_score:.3f}")

            if sharpness >= emergency_min_sharpness and quality_score >= emergency_quality_threshold:
                timestamp = frame_idx / fps if fps > 0 else 0

                frame_candidates.append({
                    'frame': frame.copy(),
                    'frame_idx': frame_idx,
                    'timestamp': timestamp,
                    'sharpness': sharpness,
                    'quality_score': quality_score,
                    'quality_metrics': quality_metrics
                })

        print(
            f"   ✅ Candidatos con umbrales de emergencia: {len(frame_candidates)}")

    if len(frame_candidates) == 0:
        print("❌ Aún no se encontraron candidatos válidos. Extrayendo los mejores disponibles...")

        # Como último recurso, tomar simplemente los mejores frames sin filtros
        all_candidates = []
        sample_indices_large = np.linspace(
            0, total_frames - 1, min(500, total_frames), dtype=int)

        for frame_idx in tqdm(sample_indices_large, desc="Evaluando todos los frames disponibles"):
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            success, frame = video.read()

            if not success:
                continue

            if force_vertical and frame.shape[1] > frame.shape[0]:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

            sharpness = calculate_frame_sharpness(frame)
            quality_score, quality_metrics = calculate_frame_quality_score(
                frame)
            timestamp = frame_idx / fps if fps > 0 else 0

            all_candidates.append({
                'frame': frame.copy(),
                'frame_idx': frame_idx,
                'timestamp': timestamp,
                'sharpness': sharpness,
                'quality_score': quality_score,
                'quality_metrics': quality_metrics
            })

        # Tomar los mejores frames disponibles
        if all_candidates:
            all_candidates.sort(key=lambda x: x['quality_score'], reverse=True)
            frame_candidates = all_candidates[:min(
                num_frames * 2, len(all_candidates))]
            print(
                f"   🆘 Seleccionados {len(frame_candidates)} mejores frames disponibles")

    if len(frame_candidates) == 0:
        raise ValueError(
            "No se encontraron frames de calidad suficiente en el video")

    # FASE 3: Selección final con filtrado de similitud
    print(f"\n🔍 Fase 3: Seleccionando mejores frames y filtrando similares...")

    # Ordenar candidatos por calidad
    frame_candidates.sort(key=lambda x: x['quality_score'], reverse=True)

    selected_frames = []
    num_frames_target = min(num_frames, len(frame_candidates))

    for candidate in frame_candidates:
        if len(selected_frames) >= num_frames_target:
            break

        # Verificar similitud con frames ya seleccionados
        is_similar = False
        for selected in selected_frames:
            similarity = calculate_frame_similarity(
                candidate['frame'], selected['frame'])
            if similarity > max_similarity:
                is_similar = True
                break

        if not is_similar:
            selected_frames.append(candidate)

    # Si no tenemos suficientes frames únicos, agregar los mejores restantes
    if len(selected_frames) < num_frames_target:
        # Crear set de IDs de frames ya seleccionados para comparación eficiente
        selected_frame_ids = {frame['frame_idx'] for frame in selected_frames}
        remaining_candidates = [
            c for c in frame_candidates if c['frame_idx'] not in selected_frame_ids]
        remaining_needed = num_frames_target - len(selected_frames)
        selected_frames.extend(remaining_candidates[:remaining_needed])

    # FASE 4: Guardar frames seleccionados
    print(
        f"\n💾 Fase 4: Guardando {len(selected_frames)} frames seleccionados...")

    # Ordenar por timestamp para mantener orden cronológico
    selected_frames.sort(key=lambda x: x['timestamp'])

    extracted_frames = []
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]

    for i, frame_data in enumerate(tqdm(selected_frames, desc="Guardando frames")):
        output_path = os.path.join(
            output_folder,
            f"frame_{i+1:03d}_{frame_data['timestamp']:.2f}s_q{frame_data['quality_score']:.3f}.jpg"
        )

        cv2.imwrite(output_path, frame_data['frame'], encode_params)
        extracted_frames.append(output_path)

        # Debug info
        metrics = frame_data['quality_metrics']
        print(f"   Frame {i+1}: Sharp={frame_data['sharpness']:.0f}, "
              f"Qual={frame_data['quality_score']:.3f}, "
              f"Tiempo={frame_data['timestamp']:.2f}s")

    video.release()

    print(f"\n🎉 Proceso completado:")
    print(f"   📁 Frames guardados en: '{output_folder}'")
    print(
        f"   📊 Frames extraídos: {len(extracted_frames)} de {total_frames} totales")
    print(
        f"   🎯 Eficiencia: {len(extracted_frames)/candidate_frames*100:.1f}% de candidatos aprobados")

    return extracted_frames

# Función simplificada para uso básico


def extract_frames_smart(video_path, output_folder="images", target_frames=None, debug=False):
    """
    Versión simplificada con configuración automática y más permisiva
    """
    return extract_frames_from_video_smart(
        video_path=video_path,
        output_folder=output_folder,
        num_frames=target_frames,  # None para cálculo automático
        quality=95,
        min_sharpness=None,  # Cálculo automático
        max_similarity=0.9,  # Permitir frames más similares
        quality_threshold=None,  # Cálculo automático
        force_vertical=True,
        debug_mode=debug
    )

# Función para casos problemáticos


def extract_frames_permissive(video_path, output_folder="images", target_frames=None):
    """
    Versión súper permisiva para videos de baja calidad
    """
    return extract_frames_from_video_smart(
        video_path=video_path,
        output_folder=output_folder,
        num_frames=target_frames,
        quality=95,
        min_sharpness=10,  # Muy permisivo
        max_similarity=0.95,  # Permitir frames muy similares
        quality_threshold=0.05,  # Súper permisivo
        force_vertical=True,
        debug_mode=True
    )
