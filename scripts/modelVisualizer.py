import pyvista as pv


def visualize_with_pyvista(model_path):
    """
    Visualiza un modelo 3D usando PyVista.

    Args:
        model_path (str): Ruta al archivo de modelo (.obj, .ply, etc.)
    """
    print(f"Cargando modelo desde: {model_path}")

    # Crear plotter
    plotter = pv.Plotter()

    # Cargar y mostrar modelo
    if model_path.endswith('.obj') or model_path.endswith('.ply'):
        mesh = pv.read(model_path)
        plotter.add_mesh(mesh, color='lightblue', show_edges=True)

        # Añadir información
        plotter.add_text(f"Vértices: {mesh.n_points}\nCaras: {mesh.n_cells}",
                         position='upper_left', font_size=12)

        # Añadir ejes
        plotter.add_axes()

        # Añadir iluminación
        plotter.add_light(pv.Light(position=(1, 1, 1)))
        plotter.add_light(pv.Light(position=(-1, -1, -1)))

        # Mostrar
        plotter.show()
    else:
        print(f"Formato de archivo no soportado: {model_path}")
