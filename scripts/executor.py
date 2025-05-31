from scripts.extractPhotosFromVideo import extract_frames_from_video_smart, extract_frames_smart
from scripts.processImage import preprocess_images_for_photogrammetry
from scripts.segmentation import segment_images_for_photogrammetry
from scripts.densify import reconstruir_con_colmap_completo
from scripts.texture import meshAndTexture


def executor():
    # extract_frames_smart("prueba.MOV", "frames_output",
    #                      target_frames=60, debug=True)

    # preprocess_images_for_photogrammetry(
    #     input_folder="images",
    #     min_resolution=720,
    #     blur_threshold=10,
    #     contrast_enhancement=1.3,
    #     brightness_adjustment=10,
    #     max_images=20,
    #     output_folder="images_preprocessed"
    # )

    segment_images_for_photogrammetry(
        input_folder="frames_output",
        output_folder_segmented="images_segmented",
        output_folder_mask="images_masks",
        model_path="models/yolo11l-seg.pt",
        confidence=0.3,
        max_workers=1,
        min_area_ratio=0.08,
        use_adaptive_confidence=True,
        prefer_centered_objects=True
    )

    # reconstruir_con_colmap_completo(
    #     images_folder="images_segmented",
    #     output_folder="reconstruction",
    # )

    # meshAndTexture(
    #     fused_ply_path="reconstruction/dense/fused.ply",
    #     output_folder="reconstruction/mesh_textured",
    #     dense_folder="reconstruction/dense",
    #     depth=12
    # )
