import os
import numpy as np
import open3d as o3d
import time


def sparse_to_dense_with_open3d(sparse_model_path, output_folder, dense_points=500000, poisson_depth=9):
    """
    Convierte nube de puntos dispersa de COLMAP a densa usando Open3D

    Args:
        sparse_model_path: Ruta a la reconstrucción dispersa de COLMAP
        output_folder: Carpeta donde guardar los resultados
        dense_points: Número de puntos en la nube densa
        poisson_depth: Profundidad para reconstrucción Poisson (8-10 recomendado)

    Returns:
        Nube de puntos densa y malla
    """
    os.makedirs(output_folder, exist_ok=True)

    start_time = time.time()
    print("Convirtiendo nube de puntos COLMAP a Open3D...")

    # Cargar puntos 3D de COLMAP
    points3D_path = os.path.join(sparse_model_path, "points3D.txt")
    if not os.path.exists(points3D_path):
        print(
            f"Error: No se encontró el archivo de puntos 3D en {points3D_path}")
        return None, None

    # Parsear puntos 3D
    points = []
    colors = []

    with open(points3D_path, 'r') as f:
        lines = f.readlines()

        # Saltar líneas de cabecera
        if lines and lines[0].startswith("#"):
            lines = lines[2:]  # Saltar las dos primeras líneas

        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 7:
                # Formato: POINT3D_ID, X, Y, Z, R, G, B, ...
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                r, g, b = int(parts[4]), int(parts[5]), int(parts[6])

                points.append([x, y, z])
                colors.append([r/255.0, g/255.0, b/255.0])

    if not points:
        print("No se pudieron cargar puntos 3D.")
        return None, None

    print(f"Cargados {len(points)} puntos 3D de la reconstrucción dispersa")

    # Crear nube de puntos Open3D
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.array(points))
    pcd.colors = o3d.utility.Vector3dVector(np.array(colors))

    # Guardar nube de puntos dispersa
    sparse_path = os.path.join(output_folder, "sparse.ply")
    o3d.io.write_point_cloud(sparse_path, pcd)
    print(f"Nube de puntos dispersa guardada en {sparse_path}")

    # Estimar normales
    print("Estimando normales...")
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(
        radius=0.1, max_nn=30))
    pcd.orient_normals_consistent_tangent_plane(k=30)

    # Aplicar reconstrucción Poisson
    print(f"Aplicando reconstrucción Poisson (profundidad={poisson_depth})...")
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=poisson_depth, width=0, scale=1.1, linear_fit=False)

    # Muestrear puntos densos de la malla
    print(f"Muestreando {dense_points} puntos de la malla...")
    dense_pcd = mesh.sample_points_poisson_disk(
        number_of_points=dense_points, init_factor=5)

    # Filtrar outliers
    print("Filtrando outliers...")
    dense_pcd, _ = dense_pcd.remove_statistical_outlier(
        nb_neighbors=20, std_ratio=2.0)

    # Guardar resultados
    dense_path = os.path.join(output_folder, "dense.ply")
    o3d.io.write_point_cloud(dense_path, dense_pcd)

    mesh_path = os.path.join(output_folder, "mesh.ply")
    o3d.io.write_triangle_mesh(mesh_path, mesh)

    elapsed_time = time.time() - start_time
    print(
        f"Proceso de densificación completado en {elapsed_time:.2f} segundos")
    print(f"Nube de puntos densa guardada en {dense_path}")
    print(f"Malla guardada en {mesh_path}")

    return dense_pcd, mesh
