from scripts.extractPhotosFromVideo import extract_frames_from_video
from scripts.processImage import preprocess_images_for_photogrammetry
from scripts.segmentation import segment_images_for_photogrammetry
from scripts.extractAndMatchFeatures import process_images_with_sift


def executor():
    # extract_frames_from_video(
    #     video_path="prueba.mp4",
    #     output_folder="images",
    #     num_frames=60
    # )

    # preprocess_images_for_photogrammetry(
    #     input_folder="images",
    #     min_resolution=720,
    #     blur_threshold=40,
    #     contrast_enhancement=1.3,
    #     brightness_adjustment=10,
    #     max_images=20,
    #     output_folder="images_preprocessed"
    # )

    # segment_images_for_photogrammetry(
    #     input_folder="images_preprocessed",
    #     output_folder_segmented="images_segmented",
    #     output_folder_mask="images_masks",
    #     model_path="models/yolo11m-seg.pt",
    #     confidence=0.6,
    #     max_workers=1
    # )

    res = process_images_with_sift("images_preprocessed")
