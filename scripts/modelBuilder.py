# reconstruction_opencv_improved.py
import os
import cv2
import numpy as np
import open3d as o3d
from pathlib import Path
from tqdm import tqdm


def run_optimized_opencv_reconstruction(input_folder, output_folder, min_matches=15):
    """
    Reconstrucción 3D optimizada para botellas usando OpenCV y Open3D.

    Args:
        input_folder (str): Carpeta con imágenes segmentadas
        output_folder (str): Carpeta para guardar resultados
        min_matches (int): Número mínimo de coincidencias entre imágenes

    Returns:
        str: Ruta al modelo 3D generado
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Cargar imágenes
    image_files = sorted([f for f in os.listdir(input_folder)
                         if f.endswith(('.jpg', '.jpeg', '.png')) and 'mask' not in f])

    if len(image_files) < 2:
        print("Se necesitan al menos 2 imágenes para la reconstrucción 3D.")
        return None

    print(f"Cargando {len(image_files)} imágenes...")
    images = []
    masks = []  # Cargar también las máscaras para mejorar la reconstrucción

    for img_file in image_files:
        img_path = os.path.join(input_folder, img_file)
        mask_path = os.path.join(input_folder, f"mask_{img_file}")

        img = cv2.imread(img_path)
        if img is not None:
            # Mejorar contraste para detectar mejor las características
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge((l, a, b))
            enhanced_img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

            images.append(enhanced_img)

            # Cargar máscara si existe
            if os.path.exists(mask_path):
                mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
                masks.append(mask)
            else:
                # Crear máscara completa si no existe
                masks.append(np.ones(img.shape[:2], dtype=np.uint8) * 255)

    # Inicializar detector de características (SIFT con parámetros mejorados)
    sift = cv2.SIFT_create(
        nfeatures=2000,            # Más características
        nOctaveLayers=5,           # Más capas por octava
        contrastThreshold=0.03,    # Menor umbral para detectar más puntos
        edgeThreshold=15,          # Mayor umbral para bordes
        sigma=1.6                  # Sigma estándar
    )

    # Extraer características de todas las imágenes
    print("Extrayendo características...")
    keypoints = []
    descriptors = []

    for i, img in enumerate(tqdm(images)):
        # Aplicar máscara para extraer características solo del objeto
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kp, desc = sift.detectAndCompute(gray, masks[i])
        keypoints.append(kp)
        descriptors.append(desc)

        # Guardar imagen con keypoints para depuración
        debug_img = cv2.drawKeypoints(
            img, kp, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        cv2.imwrite(os.path.join(output_folder,
                    f"keypoints_{i}.jpg"), debug_img)

    # Emparejar características - mejorar con emparejamiento cruzado
    print("Emparejando características...")
    matches_all = []  # Almacena emparejamientos entre todas las imágenes
    camera_indices = []  # Almacena índices de cámaras para cada emparejamiento

    # Configuración mejorada para FLANN
    FLANN_INDEX_KDTREE = 1
    # Más árboles para mejor precisión
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=8)
    search_params = dict(checks=100)  # Más comprobaciones
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    # Emparejar cada imagen con todas las demás (no solo consecutivas)
    for i in range(len(images)):
        for j in range(i+1, len(images)):
            if descriptors[i] is None or descriptors[j] is None:
                continue

            # Emparejamiento bidireccional para mayor robustez
            matches1 = flann.knnMatch(descriptors[i], descriptors[j], k=2)
            matches2 = flann.knnMatch(descriptors[j], descriptors[i], k=2)

            # Ratio test de Lowe con umbral más estricto
            good_matches1 = []
            for m, n in matches1:
                if m.distance < 0.65 * n.distance:  # Más estricto que 0.7
                    good_matches1.append(m)

            good_matches2 = []
            for m, n in matches2:
                if m.distance < 0.65 * n.distance:
                    good_matches2.append(m)

            # Verificación cruzada
            cross_matches = []
            for match1 in good_matches1:
                for match2 in good_matches2:
                    if match1.queryIdx == match2.trainIdx and match1.trainIdx == match2.queryIdx:
                        cross_matches.append(match1)
                        break

            if len(cross_matches) >= min_matches:
                matches_all.append(cross_matches)
                camera_indices.append((i, j))
                print(f"Imágenes {i}-{j}: {len(cross_matches)} coincidencias")
            else:
                print(
                    f"Imágenes {i}-{j}: Insuficientes coincidencias ({len(cross_matches)})")

    # Calibración de cámara mejorada
    print("Calibrando cámaras...")
    height, width = images[0].shape[:2]
    # Mejor estimación del punto principal y distancia focal
    focal_length = 1.5 * max(width, height)  # Factor 1.5 para botellas
    K = np.array([
        [focal_length, 0, width/2],
        [0, focal_length, height/2],
        [0, 0, 1]
    ])

    # Inicialización de Structure from Motion
    camera_matrices = [None] * len(images)
    camera_poses = [None] * len(images)

    # Inicializar primera cámara en origen
    camera_matrices[0] = K @ np.hstack((np.eye(3), np.zeros((3, 1))))
    camera_poses[0] = np.eye(4)
    camera_poses[0][:3, :3] = np.eye(3)
    camera_poses[0][:3, 3] = np.zeros(3)

    # Triangulación para múltiples vistas
    point_cloud = []
    colors = []
    point_track = {}  # Seguimiento de puntos 3D

    # Reconstrucción incremental SfM
    print("Reconstruyendo escena 3D incremental...")

    # Iniciar con el par que tiene más correspondencias
    best_match_idx = np.argmax([len(m) for m in matches_all])
    i, j = camera_indices[best_match_idx]

    # Extraer puntos correspondientes
    pts_i = np.float32(
        [keypoints[i][m.queryIdx].pt for m in matches_all[best_match_idx]])
    pts_j = np.float32(
        [keypoints[j][m.trainIdx].pt for m in matches_all[best_match_idx]])

    # Calcular matriz esencial y descomponerla
    E, mask = cv2.findEssentialMat(
        pts_i, pts_j, K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
    _, R, t, mask = cv2.recoverPose(E, pts_i, pts_j, K, mask=mask)

    # Establecer segunda cámara
    camera_matrices[j] = K @ np.hstack((R, t))
    camera_poses[j] = np.eye(4)
    camera_poses[j][:3, :3] = R
    camera_poses[j][:3, 3] = t.ravel()

    # Triangular puntos entre primera y segunda cámara
    points_4d = cv2.triangulatePoints(
        camera_matrices[0], camera_matrices[j],
        pts_i.T, pts_j.T
    )
    points_3d = (points_4d[:3] / points_4d[3]).T

    # Guardar los puntos 3D y sus correspondencias
    for idx, (pt3d, pt_i, pt_j) in enumerate(zip(points_3d, pts_i, pts_j)):
        if mask[idx]:
            point_track[(i, keypoints[i][matches_all[best_match_idx]
                         [idx].queryIdx].pt)] = len(point_cloud)
            point_track[(j, keypoints[j][matches_all[best_match_idx]
                         [idx].trainIdx].pt)] = len(point_cloud)

            # Obtener color del punto
            x, y = int(pt_i[0]), int(pt_i[1])
            if 0 <= y < images[i].shape[0] and 0 <= x < images[i].shape[1]:
                color = images[i][y, x][::-1] / 255.0  # BGR a RGB
            else:
                color = np.array([0.5, 0.5, 0.5])  # Gris por defecto

            point_cloud.append(pt3d)
            colors.append(color)

    # Procesar pares restantes
    print("Agregando cámaras adicionales...")
    for idx, (i, j) in enumerate(camera_indices):
        if idx == best_match_idx:
            continue  # Ya procesado

        if camera_matrices[i] is None or camera_matrices[j] is None:
            continue  # No podemos procesar aún

        # Triangular más puntos
        matches = matches_all[idx]
        pts_i = np.float32([keypoints[i][m.queryIdx].pt for m in matches])
        pts_j = np.float32([keypoints[j][m.trainIdx].pt for m in matches])

        # Triangular entre las cámaras
        points_4d = cv2.triangulatePoints(
            camera_matrices[i], camera_matrices[j],
            pts_i.T, pts_j.T
        )
        new_points_3d = (points_4d[:3] / points_4d[3]).T

        # Agregar nuevos puntos
        for p_idx, (pt3d, pt_i, pt_j) in enumerate(zip(new_points_3d, pts_i, pts_j)):
            key_i = (i, keypoints[i][matches[p_idx].queryIdx].pt)
            key_j = (j, keypoints[j][matches[p_idx].trainIdx].pt)

            # Si ya existe, no agregar
            if key_i in point_track or key_j in point_track:
                continue

            # Agregar nuevo punto
            point_track[key_i] = len(point_cloud)
            point_track[key_j] = len(point_cloud)

            # Obtener color
            x, y = int(pt_i[0]), int(pt_i[1])
            if 0 <= y < images[i].shape[0] and 0 <= x < images[i].shape[1]:
                color = images[i][y, x][::-1] / 255.0
            else:
                color = np.array([0.5, 0.5, 0.5])

            point_cloud.append(pt3d)
            colors.append(color)

    # Crear nube de puntos con Open3D
    if len(point_cloud) == 0:
        print("No se pudieron reconstruir puntos 3D.")
        return None

    print(f"Creando nube de puntos con {len(point_cloud)} puntos...")
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.array(point_cloud))
    pcd.colors = o3d.utility.Vector3dVector(np.array(colors))

    # Limpieza mejorada de nube de puntos
    print("Limpiando nube de puntos...")
    # 1. Eliminar outliers estadísticos con parámetros más ajustados
    pcd, inlier_idx = pcd.remove_statistical_outlier(
        nb_neighbors=30, std_ratio=1.5)

    # 2. Filtrado por distancia para eliminar puntos lejanos
    diameter = np.linalg.norm(
        np.asarray(pcd.get_max_bound()) - np.asarray(pcd.get_min_bound()))
    pcd, _ = pcd.remove_radius_outlier(nb_points=20, radius=diameter * 0.05)

    # 3. Submuestreo para reducir ruido
    pcd = pcd.voxel_down_sample(voxel_size=diameter * 0.005)

    # Guardar nube de puntos
    pcd_file = os.path.join(output_folder, "points.ply")
    o3d.io.write_point_cloud(pcd_file, pcd)

    # Reconstrucción de malla mejorada para botellas
    print("Generando malla 3D optimizada para botella...")

    # Estimación de normales más robusta orientada hacia afuera
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(
        radius=diameter * 0.03, max_nn=50))

    # Orientar normales de manera consistente - importante para botellas
    pcd.orient_normals_consistent_tangent_plane(30)

    # Reconstrucción con Poisson optimizada para botellas
    print("Aplicando reconstrucción Poisson con parámetros optimizados...")
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd,
        depth=10,        # Mayor profundidad para detalles
        width=0,         # Ancho 0 para considerar todos los puntos
        scale=1.1,       # Escala ligeramente mayor para botellas
        linear_fit=False  # Desactivar para objetos cerrados como botellas
    )

    # Filtrado basado en densidad para remover triángulos erróneos
    densities = np.asarray(densities)
    density_threshold = np.quantile(densities, 0.05)  # Eliminar 5% inferior
    vertices_to_remove = densities < density_threshold
    mesh.remove_vertices_by_mask(vertices_to_remove)

    # Limpieza de malla
    mesh.remove_degenerate_triangles()
    mesh.remove_duplicated_triangles()
    mesh.remove_duplicated_vertices()
    mesh.remove_non_manifold_edges()

    # Suavizado adicional para botellas
    mesh = mesh.filter_smooth_taubin(number_of_iterations=20)

    # Guardar malla
    mesh_file = os.path.join(output_folder, "model.obj")
    o3d.io.write_triangle_mesh(mesh_file, mesh)

    # Crear visualización para depuración
    vis_file = os.path.join(output_folder, "visualization.png")
    visualize_and_save(mesh, vis_file)

    print(
        f"Reconstrucción 3D optimizada completada. Modelo guardado en: {mesh_file}")
    return mesh_file


def visualize_and_save(mesh, output_file):
    """
    Visualiza y guarda una imagen de la malla 3D.
    """
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False)
    vis.add_geometry(mesh)

    # Configurar iluminación y cámara
    render_option = vis.get_render_option()
    render_option.mesh_show_wireframe = True
    render_option.light_on = True
    render_option.background_color = np.array([1, 1, 1])  # Fondo blanco

    # Configurar vista
    view_control = vis.get_view_control()
    view_control.set_zoom(1.5)

    # Renderizar y guardar
    vis.update_geometry(mesh)
    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(output_file)
    vis.destroy_window()
