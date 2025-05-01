from scripts.executor import executor

if __name__ == "__main__":
    executor()

# import cv2
# import numpy as np
# from ultralytics import YOLO

# model = YOLO("models/yolo11n-seg.pt")

# image_path = "images/g.jpeg"

# original_image = cv2.imread(image_path)
# if original_image is None:
#     print(f"Error: No se pudo cargar la imagen desde {image_path}")
#     exit()

# results = model(image_path)

# if results[0].masks is not None and len(results[0].masks) > 0:

#     mask = results[0].masks[0].data.cpu().numpy()[0]

#     print(f"Forma de la máscara original: {mask.shape}")
#     print(f"Forma de la imagen original: {original_image.shape}")

#     if len(mask.shape) > 2:
#         mask = mask[0]

#     mask = cv2.resize(mask, (original_image.shape[1], original_image.shape[0]))

#     mask = (mask > 0.5).astype(np.uint8)

#     colored_mask = np.zeros_like(original_image, dtype=np.uint8)
#     colored_mask[mask == 1] = [0, 255, 0]

#     alpha = 0.5
#     output = cv2.addWeighted(original_image, 1, colored_mask, alpha, 0)

#     output = cv2.resize(output, (1280, 720))
#     cv2.imshow("Primera máscara detectada", output)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
# else:

#     original_image = cv2.resize(original_image, (1280, 720))
#     print("No se encontraron objetos segmentables en la imagen.")
#     cv2.imshow("Imagen original", original_image)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
