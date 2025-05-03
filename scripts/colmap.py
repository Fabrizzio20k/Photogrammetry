import time
import os
import cv2
import numpy as np
import subprocess
import sqlite3


def colmap_reconstruction_from_sift(images_folder, output_folder):
    """
    Realiza una reconstrucción 3D usando COLMAP a partir de matches SIFT
    """
    os.makedirs(output_folder, exist_ok=True)

    # Crear carpetas
    sparse_folder = os.path.join(output_folder, "sparse")
    os.makedirs(sparse_folder, exist_ok=True)

    database_path = os.path.join(output_folder, "database.db")

    # Eliminar base de datos si existe
    if os.path.exists(database_path):
        os.remove(database_path)

    # Crear base de datos COLMAP
    print("Creando base de datos COLMAP...")
    subprocess.run(["colmap", "database_creator",
                    "--database_path", database_path],
                   check=True)

    # Extraer características usando COLMAP
    print("Extrayendo características con COLMAP...")
    subprocess.run([
        "colmap", "feature_extractor",
        "--database_path", database_path,
        "--image_path", images_folder,
        "--ImageReader.camera_model", "SIMPLE_RADIAL",
        "--ImageReader.single_camera", "1"
    ], check=True)

    # Ahora necesitamos hacer el matching con COLMAP en vez de usar nuestros matches
    # porque es más fácil que importar nuestros matches manualmente
    print("Emparejando características con COLMAP (exhaustive matcher)...")
    subprocess.run([
        "colmap", "exhaustive_matcher",
        "--database_path", database_path,
    ], check=True)

    # Ejecutar triangulación
    print("Ejecutando triangulación con COLMAP...")
    subprocess.run([
        "colmap", "mapper",
        "--database_path", database_path,
        "--image_path", images_folder,
        "--output_path", sparse_folder
    ], check=True)

    # Verificar reconstrucción
    if os.path.exists(os.path.join(sparse_folder, "0")):
        print(f"Reconstrucción exitosa en {os.path.join(sparse_folder, '0')}")
        return os.path.join(sparse_folder, "0")
    else:
        reconstructions = [f for f in os.listdir(sparse_folder)
                           if os.path.isdir(os.path.join(sparse_folder, f))]
        if reconstructions:
            print(
                f"Reconstrucción exitosa en {os.path.join(sparse_folder, reconstructions[0])}")
            return os.path.join(sparse_folder, reconstructions[0])
        else:
            print("No se encontró ninguna reconstrucción")
            return None


def reconstruir_con_colmap_completo(images_folder, output_folder):
    """
    Realiza una reconstrucción completa con COLMAP usando todos sus pasos
    """
    os.makedirs(output_folder, exist_ok=True)

    # Crear subcarpetas
    sparse_folder = os.path.join(output_folder, "sparse")
    os.makedirs(sparse_folder, exist_ok=True)

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
        "--ImageReader.camera_model", "SIMPLE_RADIAL",
        "--ImageReader.single_camera", "1",
        "--SiftExtraction.use_gpu", "0",  # Para Mac sin GPU NVIDIA
        "--SiftExtraction.max_num_features", "8192",  # Más características
        "--SiftExtraction.first_octave", "-1",  # Para capturar más detalles
    ], check=True)

    # 3. Hacer matching con múltiples estrategias
    print("Realizando matching de características...")

    # Primero exhaustive matching
    subprocess.run([
        "colmap", "exhaustive_matcher",
        "--database_path", database_path,
        "--SiftMatching.use_gpu", "0",  # Para Mac sin GPU NVIDIA
        "--SiftMatching.guided_matching", "1",  # Matching guiado para mejorar
        "--SiftMatching.max_num_matches", "32768",  # Permitir más matches
        # Más permisivo (0.8 es el valor por defecto)
        "--SiftMatching.max_ratio", "0.9",
    ], check=True)

    # 4. Mapper con parámetros más permisivos
    print("Ejecutando triangulación con COLMAP...")
    subprocess.run([
        "colmap", "mapper",
        "--database_path", database_path,
        "--image_path", images_folder,
        "--output_path", sparse_folder,
        "--Mapper.min_num_matches", "8",  # Valor más bajo (default es 15)
        "--Mapper.init_min_num_inliers", "8",  # Valor más bajo
        "--Mapper.abs_pose_min_num_inliers", "8",  # Valor más bajo
        "--Mapper.abs_pose_min_inlier_ratio", "0.1",  # Más permisivo
        "--Mapper.ba_global_max_num_iterations", "50",  # Más iteraciones
        "--Mapper.ba_local_max_num_iterations", "30",  # Más iteraciones
    ], check=True)

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
        points3D_path = os.path.join(reconstruction_path, "points3D.txt")
        if os.path.exists(points3D_path):
            with open(points3D_path, 'r') as f:
                lines = f.readlines()
                num_points = len([l for l in lines if not l.startswith('#')])
                print(
                    f"Reconstrucción exitosa con {num_points} puntos 3D en {reconstruction_path}")
                return reconstruction_path
        else:
            print(
                f"La reconstrucción en {reconstruction_path} no contiene puntos 3D")

    print("No se pudo generar una reconstrucción con puntos 3D")
    return None
