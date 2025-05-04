import os
import subprocess
from shutil import rmtree


def reconstruir_con_colmap_completo(images_folder, output_folder):
    """
    Realiza una reconstrucción completa con COLMAP usando todos sus pasos
    """
    if os.path.exists(output_folder):
        rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    # Crear subcarpetas
    sparse_folder = os.path.join(output_folder, "sparse")
    dense_folder = os.path.join(output_folder, "dense")
    os.makedirs(sparse_folder, exist_ok=True)
    os.makedirs(dense_folder, exist_ok=True)

    database_path = os.path.join(output_folder, "database.db")

    # Eliminar base de datos si existe
    if os.path.exists(database_path):
        os.remove(database_path)

    # 1. Crear base de datos
    print("Creando base de datos COLMAP...")
    subprocess.run(["colmap", "database_creator",
                    "--database_path", database_path],
                   check=True)

    # 2. Extraer características con parámetros más permisivos
    print("Extrayendo características...")
    subprocess.run([
        "colmap", "feature_extractor",
        "--database_path", database_path,
        "--image_path", images_folder,
        "--ImageReader.camera_model", "RADIAL",
        "--ImageReader.single_camera", "1",
        "--SiftExtraction.use_gpu", "0",
        "--SiftExtraction.max_num_features", "16384",
        "--SiftExtraction.first_octave", "-1",
    ], check=True)

    # 3. Hacer matching con exhaustive_matcher
    print("Realizando matching de características...")
    subprocess.run([
        "colmap", "exhaustive_matcher",
        "--database_path", database_path,
        "--SiftMatching.use_gpu", "0",
        "--SiftMatching.guided_matching", "1",
        "--SiftMatching.max_ratio", "0.85",
        "--SiftMatching.max_num_matches", "32768",
    ], check=True)

    # 4. Mapper con parámetros más permisivos pero no demasiado
    print("Ejecutando triangulación con COLMAP...")
    subprocess.run([
        "colmap", "mapper",
        "--database_path", database_path,
        "--image_path", images_folder,
        "--output_path", sparse_folder,
        "--Mapper.min_num_matches", "10",
        "--Mapper.init_min_num_inliers", "10",
        "--Mapper.abs_pose_min_inlier_ratio", "0.15",
        "--Mapper.ba_global_max_num_iterations", "50",
        "--Mapper.ba_local_max_num_iterations", "30",
    ], check=True)

    # AÑADIR AQUÍ: Refinamiento adicional con bundle adjuster
    print("Refinando posiciones de cámaras con bundle adjustment...")
    # Buscar el modelo reconstruido (generalmente en sparse/0)
    reconstructed_model = None
    if os.path.exists(os.path.join(sparse_folder, "0")):
        reconstructed_model = os.path.join(sparse_folder, "0")
    else:
        reconstructions = [f for f in os.listdir(sparse_folder)
                           if os.path.isdir(os.path.join(sparse_folder, f))]
        if reconstructions:
            reconstructed_model = os.path.join(
                sparse_folder, reconstructions[0])

    if reconstructed_model:
        # Ejecutar bundle adjustment para refinamiento adicional
        subprocess.run([
            "colmap", "bundle_adjuster",
            "--input_path", reconstructed_model,
            "--output_path", reconstructed_model,
            "--BundleAdjustment.max_num_iterations", "100",
            "--BundleAdjustment.refine_focal_length", "1",
            "--BundleAdjustment.refine_principal_point", "1",
            "--BundleAdjustment.refine_extra_params", "1"
        ], check=True)
        print("Refinamiento de cámaras completado")

    # Verificar reconstrucción
    reconstruction_path = None
    if os.path.exists(os.path.join(sparse_folder, "0")):
        reconstruction_path = os.path.join(sparse_folder, "0")
    else:
        reconstructions = [f for f in os.listdir(sparse_folder)
                           if os.path.isdir(os.path.join(sparse_folder, f))]
        if reconstructions:
            reconstruction_path = os.path.join(
                sparse_folder, reconstructions[0])

    if reconstruction_path:
        # Verificar que realmente contiene puntos 3D
        points3D_path = os.path.join(reconstruction_path, "points3D.bin")
        if not os.path.exists(points3D_path):
            points3D_path = os.path.join(reconstruction_path, "points3D.txt")

        if os.path.exists(points3D_path) and os.path.getsize(points3D_path) > 0:
            print(f"Reconstrucción sparse exitosa en {reconstruction_path}")

            # Completamos el proceso con la función de completar_fotogrametria
            completar_fotogrametria(
                sparse_folder, images_folder, output_folder)

            return reconstruction_path
        else:
            print(
                f"La reconstrucción en {reconstruction_path} no contiene puntos 3D válidos")

    print("No se pudo generar una reconstrucción con puntos 3D")
    return None


def completar_fotogrametria(sparse_folder, images_folder, output_folder):
    """
    Completa el proceso de fotogrametría a partir de una reconstrucción sparse existente
    """
    # Encontrar la reconstrucción sparse
    if os.path.exists(os.path.join(sparse_folder, "0")):
        reconstruction_path = os.path.join(sparse_folder, "0")
    else:
        reconstructions = [f for f in os.listdir(sparse_folder)
                           if os.path.isdir(os.path.join(sparse_folder, f))]
        if reconstructions:
            reconstruction_path = os.path.join(
                sparse_folder, reconstructions[0])
        else:
            print("No se encontró reconstrucción sparse.")
            return False

    # Crear carpetas necesarias
    dense_folder = os.path.join(output_folder, "dense")
    mesh_folder = os.path.join(output_folder, "mesh")
    textured_folder = os.path.join(output_folder, "textured")

    os.makedirs(dense_folder, exist_ok=True)
    os.makedirs(mesh_folder, exist_ok=True)
    os.makedirs(textured_folder, exist_ok=True)

    # 1. Undistort images
    print("Preparando imágenes para reconstrucción densa...")
    subprocess.run([
        "colmap", "image_undistorter",
        "--image_path", images_folder,
        "--input_path", reconstruction_path,
        "--output_path", dense_folder,
        "--output_type", "COLMAP"
    ], check=True)

    # Con estas líneas mejoradas:
    print("Calculando mapas de profundidad de alta precisión...")
    subprocess.run([
        "colmap", "patch_match_stereo",
        "--workspace_path", dense_folder,
        "--workspace_format", "COLMAP",
        "--PatchMatchStereo.geom_consistency", "1",
        "--PatchMatchStereo.max_image_size", "3200",  # Mayor resolución
        "--PatchMatchStereo.window_radius", "5",      # Mejor precisión
        "--PatchMatchStereo.window_step", "1",        # Paso más fino
        "--PatchMatchStereo.filter", "1",             # Filtrado mejorado
        # Más permisivo para capturar más detalles
        "--PatchMatchStereo.filter_min_ncc", "0.1",
        # Ángulo mínimo más pequeño
        "--PatchMatchStereo.filter_min_triangulation_angle", "3.0",
        # Usar más memoria para mejor rendimiento
        "--PatchMatchStereo.cache_size", "32"
    ], check=True)

    # 3. Generate dense point cloud
    print("Fusionando mapas de profundidad en nube de puntos densa...")
    fused_ply_path = os.path.join(dense_folder, "fused.ply")
    subprocess.run([
        "colmap", "stereo_fusion",
        "--workspace_path", dense_folder,
        "--workspace_format", "COLMAP",
        "--input_type", "geometric",
        "--output_path", fused_ply_path
    ], check=True)

    # 4. Convertir sparse model a PLY también (pero no imprimir esto)
    sparse_ply_path = os.path.join(output_folder, "sparse.ply")
    subprocess.run([
        "colmap", "model_converter",
        "--input_path", reconstruction_path,
        "--output_path", sparse_ply_path,
        "--output_type", "PLY"
    ], check=True)

    # En lugar de imprimir información sobre el sparse model,
    # ahora solo imprimos información sobre el modelo denso
    print(f"Reconstrucción completa con éxito!")
    print(f"Nube de puntos densa generada en: {fused_ply_path}")
    print(f"Este archivo puede ser abierto directamente en MeshLab o CloudCompare para visualización y procesamiento adicional.")

    return True
