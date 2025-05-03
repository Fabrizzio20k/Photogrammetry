from scripts.extractPhotosFromVideo import extract_frames_from_video
from scripts.processImage import preprocess_images_for_photogrammetry
from scripts.segmentation import segment_images_for_photogrammetry
from scripts.extractAndMatchFeatures import process_images_with_sift
from scripts.colmap import colmap_reconstruction_from_sift
from scripts.densify import sparse_to_dense_with_open3d


def executor():
    # extract_frames_from_video(
    #     video_path="prueba.MOV",
    #     output_folder="images",
    #     num_frames=30
    # )

    # preprocess_images_for_photogrammetry(
    #     input_folder="images",
    #     min_resolution=720,
    #     blur_threshold=10,
    #     contrast_enhancement=1.3,
    #     brightness_adjustment=10,
    #     max_images=20,
    #     output_folder="images_preprocessed"
    # )

    # segment_images_for_photogrammetry(
    #     input_folder="images_preprocessed",
    #     output_folder_segmented="images_segmented",
    #     output_folder_mask="images_masks",
    #     model_path="models/yolo11l-seg.pt",
    #     confidence=0.2,
    #     max_workers=1
    # )

    colmap_reconstruction_from_sift(
        images_folder="images_preprocessed",
        output_folder="reconstruction",
    )
    # dense_pcd, mesh = sparse_to_dense_with_open3d(
    #     sparse_model_path="reconstruction/sparse/0",
    #     output_folder="reconstruction/dense",
    #     dense_points=500000,
    #     poisson_depth=10
    # )
