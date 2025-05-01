from scripts.extractPhotosFromVideo import extract_frames_from_video
from scripts.processImage import preprocess_images_for_photogrammetry
from scripts.segmentation import segment_images_for_photogrammetry
from scripts.modelBuilder import run_optimized_opencv_reconstruction
from scripts.modelVisualizer import visualize_with_pyvista


def executor():
    extract_frames_from_video(
        video_path="prueba.mp4",
        output_folder="images",
        num_frames=60
    )

    preprocess_images_for_photogrammetry(
        input_folder="images",
        min_resolution=720,
        blur_threshold=40,
        contrast_enhancement=1.3,
        brightness_adjustment=10,
        max_images=20,
        output_folder="images_preprocessed"
    )

    segment_images_for_photogrammetry(
        input_folder="images_preprocessed",
        output_folder_segmented="images_segmented",
        output_folder_mask="images_masks",
        model_path="models/yolo11m-seg.pt",
        confidence=0.6,
        max_workers=1
    )

    # run_optimized_opencv_reconstruction(
    #     input_folder="images_segmented",
    #     output_folder="3d_model",
    #     min_matches=10
    # )

    # visualize_with_pyvista(
    #     model_path="3d_model/fused.ply"
    # )
