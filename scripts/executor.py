from scripts.extractPhotosFromVideo import extract_frames_from_video
from scripts.processImage import preprocess_images_for_photogrammetry


def executor():
    # PASO 1: Extraer frames del video
    extract_frames_from_video(
        video_path="prueba.mp4",
        output_folder="images",
        num_frames=25
    )

    imagenes_optimizadas = preprocess_images_for_photogrammetry(
        input_folder="images",
        min_resolution=1800,
        blur_threshold=80,
        contrast_enhancement=1.3,
        brightness_adjustment=10,
        max_images=20
    )
