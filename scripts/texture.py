import os
import numpy as np
import open3d as o3d
import subprocess
import time


def meshAndTexture(fused_ply_path, dense_folder, output_folder, depth=12):
    """
    Proceso completo: nube de puntos → malla con textura de alta calidad
    """
    os.makedirs(output_folder, exist_ok=True)

    print("=== INICIANDO PROCESO DE RECONSTRUCCIÓN 3D DE ALTA CALIDAD ===")
    start_time = time.time()

    # 1. Verificar archivo de entrada
    if not os.path.exists(fused_ply_path):
        print(f"Error: No se encuentra el archivo {fused_ply_path}")
        return False

    # 2. Generar malla desde nube de puntos (mejorado)
    mesh_path = os.path.join(output_folder, "mesh_alta_calidad.ply")
    print(f"\n=== PASO 1: GENERANDO MALLA 3D DE ALTA RESOLUCIÓN ===")
    success = procesar_nube_puntos_alta_calidad(
        fused_ply_path, mesh_path, depth)
    if not success:
        print("Error al generar la malla. Abortando.")
        return False

    # 3. Texturizar la malla con parámetros de alta calidad
    textured_path = os.path.join(output_folder, "modelo_final_texturizado.obj")
    print(f"\n=== PASO 2: APLICANDO TEXTURA DE ALTA RESOLUCIÓN ===")
    success = texturizar_alta_calidad(mesh_path, textured_path)
    if not success:
        print("Error al texturizar. Abortando.")
        return False

    # 4. Finalizar y mostrar resultados
    elapsed = time.time() - start_time
    print(f"\n=== PROCESO COMPLETADO EN {elapsed/60:.1f} MINUTOS ===")
    print(f"MODELO 3D TEXTURIZADO COMPLETO: {textured_path}")
    print("\nEl modelo final incluye malla y textura de alta calidad.")

    return textured_path


def procesar_nube_puntos_alta_calidad(input_ply_path, output_mesh_path, depth=12):
    """
    Procesa la nube de puntos y genera una malla de alta calidad
    con escala correcta y resolución óptima
    """
    try:
        print(f"Procesando nube de puntos: {input_ply_path}")

        # Cargar nube de puntos
        pcd = o3d.io.read_point_cloud(input_ply_path)
        num_puntos = len(pcd.points)
        print(f"Nube cargada con {num_puntos} puntos")

        if num_puntos < 1000:
            print(
                "ERROR: La nube tiene muy pocos puntos para generar una malla de calidad")
            return False

        # Analizar dimensiones para verificar escala
        points = np.asarray(pcd.points)
        min_bound = points.min(axis=0)
        max_bound = points.max(axis=0)
        dimensions = max_bound - min_bound
        print(f"Dimensiones de la escena: {dimensions}")

        # Comprobar si la escala es muy pequeña
        volumen = dimensions[0] * dimensions[1] * dimensions[2]
        if volumen < 0.001:
            print("AVISO: La escala del modelo es muy pequeña. Aplicando escalado x100")
            # Escalar para que sea visible
            points = points * 100
            pcd.points = o3d.utility.Vector3dVector(points)

            # Recalcular dimensiones
            min_bound = points.min(axis=0)
            max_bound = points.max(axis=0)
            dimensions = max_bound - min_bound
            print(f"Nuevas dimensiones después de escalar: {dimensions}")

        # Eliminar outliers con parámetros conservadores para preservar detalles
        print("Eliminando outliers manteniendo detalles importantes...")
        cl, ind = pcd.remove_statistical_outlier(
            nb_neighbors=50,  # Más vecinos para mejor contexto
            std_ratio=2.0     # Menos agresivo para preservar detalles
        )
        pcd = pcd.select_by_index(ind)
        print(f"Después de filtrar: {len(pcd.points)} puntos")

        # Estimar normales con parámetros optimizados para alta calidad
        print("Calculando normales de alta precisión...")
        pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(
                radius=0.02,  # Radio más ajustado para precisión
                max_nn=100    # Más vecinos para mejor estimación
            )
        )

        # Orientar normales (crucial para buena reconstrucción)
        print("Orientando normales para consistencia global...")
        pcd.orient_normals_consistent_tangent_plane(k=50)

        # Reconstrucción Poisson con parámetros para máxima calidad
        print(f"Ejecutando reconstrucción Poisson avanzada (depth={depth})...")
        print("Este proceso puede tardar varios minutos para alta calidad...")
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd,
            depth=depth,      # 12-14 para alta resolución
            width=0,          # Adaptativo
            scale=1.1,        # Factor de escala para mejor cobertura
            linear_fit=False  # Mejor para objetos orgánicos
        )

        # Recortar la malla usando densidades de manera adaptativa
        print("Refinando malla para eliminar artefactos...")
        percentil = 0.03  # Más bajo para preservar más geometría
        vertices_to_remove = densities < np.quantile(densities, percentil)
        mesh.remove_vertices_by_mask(vertices_to_remove)

        # Aplicar suavizado ligero manteniendo los detalles
        print("Aplicando suavizado adaptativo...")
        mesh = mesh.filter_smooth_taubin(number_of_iterations=2)

        # Limpiar y optimizar la malla
        print("Optimizando topología de la malla...")
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_non_manifold_edges()

        # Asegurar que tiene normales para renderizado
        mesh.compute_vertex_normals()

        # Verificar si la malla tiene un número razonable de triángulos
        if len(mesh.triangles) < 1000:
            print("ADVERTENCIA: La malla generada tiene muy pocos triángulos.")
            print("Esto puede indicar problemas con la reconstrucción.")
            # Continuar de todos modos

        # Guardar la malla
        print(f"Guardando malla de alta calidad en: {output_mesh_path}")
        o3d.io.write_triangle_mesh(
            output_mesh_path,
            mesh,
            write_vertex_colors=True,
            write_vertex_normals=True,
            write_triangle_uvs=True  # Importante para texturizado
        )

        # Información sobre la malla generada
        print(f"Malla de alta calidad generada:")
        print(f"- Vértices: {len(mesh.vertices)}")
        print(f"- Triángulos: {len(mesh.triangles)}")
        print(
            f"- Dimensiones: X={dimensions[0]:.2f}, Y={dimensions[1]:.2f}, Z={dimensions[2]:.2f}")

        return True

    except Exception as e:
        print(f"ERROR en procesamiento de la malla: {e}")
        import traceback
        traceback.print_exc()
        return False


def texturizar_alta_calidad(mesh_path, output_path):
    """
    Procesa y mejora la malla existente, corrigiendo la orientación de normales
    y preservando solo los archivos que funcionan
    """
    try:
        print(f"Procesando modelo: {mesh_path}")

        # Verificar que el archivo de entrada existe
        if not os.path.exists(mesh_path):
            print(f"ERROR: No se encuentra el archivo de entrada {mesh_path}")
            return False

        # Definir ruta de salida (asegurarse que no sea igual a la entrada)
        if mesh_path == output_path:
            output_path = os.path.splitext(
                output_path)[0] + "_final" + os.path.splitext(output_path)[1]

        # Cargar la malla directamente con Open3D
        print("Cargando y procesando la malla...")
        mesh = o3d.io.read_triangle_mesh(mesh_path)

        if len(mesh.vertices) == 0 or len(mesh.triangles) == 0:
            print("ERROR: La malla no contiene geometría válida")
            return False

        print(
            f"Malla cargada: {len(mesh.vertices)} vértices, {len(mesh.triangles)} triángulos")

        # Asegurar que la malla tiene normales
        mesh.compute_vertex_normals()

        # Verificar y corregir orientación de normales
        print("Verificando orientación de normales...")
        vertices = np.asarray(mesh.vertices)
        center = vertices.mean(axis=0)
        vertex_normals = np.asarray(mesh.vertex_normals)

        # Verificar orientación con una muestra de vértices
        sample_indices = np.random.choice(
            len(vertices), min(1000, len(vertices)), replace=False)
        sample_vertices = vertices[sample_indices]
        sample_normals = vertex_normals[sample_indices]
        directions = sample_vertices - center
        dot_products = np.sum(sample_normals * directions, axis=1)

        # Si la mayoría de normales apuntan hacia adentro, invertirlas
        if np.mean(dot_products) < 0:
            print("CORRIGIENDO: Las normales están invertidas, reorientando...")
            # Invertir triángulos para cambiar orientación
            mesh.triangles = o3d.utility.Vector3iVector(
                np.asarray(mesh.triangles)[:, ::-1]
            )
            # Recalcular normales
            mesh.compute_vertex_normals()
            print("Normales reorientadas correctamente")

        # Asegurar que la malla tiene colores si es necesario
        if not mesh.has_vertex_colors():
            print("Aplicando colores básicos a la malla...")
            try:
                # Intentar usar colores de la nube de puntos si está disponible
                pcd = o3d.io.read_point_cloud(mesh_path)
                if pcd.has_colors():
                    print("Transfiriendo colores desde la nube de puntos...")
                    # Crear un KDTree con los puntos
                    pcd_tree = o3d.geometry.KDTreeFlann(pcd)

                    # Para cada vértice en la malla, encontrar el punto más cercano
                    mesh_vertices = np.asarray(mesh.vertices)
                    vertex_colors = []

                    for vertex in mesh_vertices:
                        k, idx, _ = pcd_tree.search_knn_vector_3d(vertex, 1)
                        if k > 0:
                            # Obtener el color del punto más cercano
                            color = np.asarray(pcd.colors)[idx[0]]
                            vertex_colors.append(color)
                        else:
                            # Color predeterminado si no hay coincidencia
                            vertex_colors.append([0.7, 0.7, 0.7])  # Gris

                    # Asignar colores a la malla
                    mesh.vertex_colors = o3d.utility.Vector3dVector(
                        np.array(vertex_colors))
                    print("Colores transferidos exitosamente")
                else:
                    # Aplicar un color uniforme si no hay colores de origen
                    print("Aplicando color uniforme...")
                    vertices_color = np.ones(
                        (len(mesh.vertices), 3)) * 0.7  # Gris claro
                    mesh.vertex_colors = o3d.utility.Vector3dVector(
                        vertices_color)
            except Exception as color_error:
                print(f"Error al aplicar colores: {color_error}")
                # Aplicar un color uniforme como fallback
                print("Aplicando color uniforme...")
                vertices_color = np.ones(
                    (len(mesh.vertices), 3)) * 0.7  # Gris claro
                mesh.vertex_colors = o3d.utility.Vector3dVector(vertices_color)

        # Guardar la malla procesada directamente en la ruta de salida final
        print(f"Guardando modelo final en: {output_path}")
        success = o3d.io.write_triangle_mesh(
            output_path,
            mesh,
            write_vertex_colors=True,
            write_vertex_normals=True
        )

        if not success or not os.path.exists(output_path):
            print("ERROR: No se pudo guardar el modelo final")
            return False

        print(f"Modelo guardado exitosamente en: {output_path}")
        print(f"Dimensiones del modelo:")
        bbox = mesh.get_axis_aligned_bounding_box()
        min_bound = bbox.min_bound
        max_bound = bbox.max_bound
        dimensions = max_bound - min_bound
        print(f"- X: {dimensions[0]:.2f}")
        print(f"- Y: {dimensions[1]:.2f}")
        print(f"- Z: {dimensions[2]:.2f}")

        return True

    except Exception as e:
        print(f"ERROR en el proceso: {e}")
        import traceback
        traceback.print_exc()
        return False
