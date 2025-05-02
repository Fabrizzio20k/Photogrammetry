import os
import cv2
import numpy
import matplotlib.pyplot as plt


def process_images_with_sift(image_folder):
    """
    Procesa imágenes usando SIFT para extracción y emparejamiento de características

    Args:
        image_folder: Ruta al directorio que contiene las imágenes

    Returns:
        matches_dict: Diccionario con pares de imágenes como claves y sus correspondencias
    """

    image_files = [f for f in os.listdir(image_folder)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    images = {}
    for img_file in image_files:
        img_path = os.path.join(image_folder, img_file)
        images[img_file] = cv2.imread(img_path)

    print(f"Cargadas {len(images)} imágenes")

    sift = cv2.SIFT_create()

    descriptors = {}
    keypoints = {}

    for img_name, img in images.items():
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        kp, des = sift.detectAndCompute(gray, None)

        keypoints[img_name] = kp
        descriptors[img_name] = des

        print(f"Imagen {img_name}: {len(kp)} keypoints detectados")

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches_dict = {}

    image_names = list(images.keys())
    for i in range(len(image_names)):
        for j in range(i+1, len(image_names)):
            img1_name = image_names[i]
            img2_name = image_names[j]

            if descriptors[img1_name] is None or descriptors[img2_name] is None:
                continue

            matches = flann.knnMatch(
                descriptors[img1_name], descriptors[img2_name], k=2)

            good_matches = []
            for m, n in matches:
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)

            pair_key = f"{img1_name}-{img2_name}"
            matches_dict[pair_key] = {
                'keypoints1': keypoints[img1_name],
                'keypoints2': keypoints[img2_name],
                'matches': good_matches
            }

            print(f"Par {pair_key}: {len(good_matches)} buenos emparejamientos")

    if matches_dict:
        pair_key = list(matches_dict.keys())[0]
        img1_name, img2_name = pair_key.split('-')

        img1 = images[img1_name]
        img2 = images[img2_name]
        kp1 = matches_dict[pair_key]['keypoints1']
        kp2 = matches_dict[pair_key]['keypoints2']
        good_matches = matches_dict[pair_key]['matches']

        img_matches = cv2.drawMatches(
            img1, kp1, img2, kp2, good_matches, None,
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
        )

        plt.figure(figsize=(15, 8))
        plt.imshow(cv2.cvtColor(img_matches, cv2.COLOR_BGR2RGB))
        plt.title(f'Emparejamientos SIFT: {pair_key}')
        plt.savefig(os.path.join(image_folder, 'sift_matches.jpg'))
        plt.close()

    return matches_dict
