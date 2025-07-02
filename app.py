import base64
import time
import subprocess
import os
import zipfile
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from utils.extractPhotosFromVideo import extract_frames_smart
from fastapi.responses import FileResponse, Response
import cv2
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_mesh_statistics(obj_file_path):
    """
    Extrae estadísticas básicas de un archivo OBJ
    """
    if not os.path.exists(obj_file_path):
        return None

    vertices = 0
    faces = 0
    texture_coords = 0
    normals = 0

    try:
        with open(obj_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('v '):  # Vertex
                    vertices += 1
                elif line.startswith('f '):  # Face
                    faces += 1
                elif line.startswith('vt '):  # Texture coordinate
                    texture_coords += 1
                elif line.startswith('vn '):  # Vertex normal
                    normals += 1

        # Calcular triángulos (la mayoría de faces en fotogrametría son triángulos)
        triangles = faces  # Asumir que cada face es un triángulo

        # Calcular tamaño del archivo
        file_size_bytes = os.path.getsize(obj_file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)

        return {
            "vertices": vertices,
            "faces": faces,
            "triangles": triangles,  # Generalmente faces = triangles en fotogrametría
            "texture_coordinates": texture_coords,
            "vertex_normals": normals,
            "file_size_bytes": file_size_bytes,
            "file_size_mb": round(file_size_mb, 2)
        }

    except Exception as e:
        print(f"Error leyendo estadísticas del mesh: {e}")
        return None


def get_texture_files_info(data_folder):
    """
    Obtiene información sobre los archivos de textura
    """
    texture_files = [f for f in os.listdir(data_folder)
                     if f.lower().endswith(('.jpg', '.jpeg', '.png')) and 'texture' in f.lower()]

    texture_info = []
    total_texture_size = 0

    for texture_file in texture_files:
        texture_path = os.path.join(data_folder, texture_file)
        if os.path.exists(texture_path):
            size_bytes = os.path.getsize(texture_path)
            total_texture_size += size_bytes

            # Obtener dimensiones de la textura
            try:
                import cv2
                img = cv2.imread(texture_path)
                if img is not None:
                    height, width = img.shape[:2]
                    texture_info.append({
                        "filename": texture_file,
                        "size_bytes": size_bytes,
                        "size_mb": round(size_bytes / (1024 * 1024), 2),
                        "width": width,
                        "height": height,
                        "resolution": f"{width}x{height}"
                    })
            except:
                texture_info.append({
                    "filename": texture_file,
                    "size_bytes": size_bytes,
                    "size_mb": round(size_bytes / (1024 * 1024), 2)
                })

    return {
        "texture_files": texture_info,
        "total_textures": len(texture_files),
        "total_texture_size_mb": round(total_texture_size / (1024 * 1024), 2)
    }


class PhotoSelectionRequest(BaseModel):
    selected_photos: List[str]


def run_command(cmd, timeout=300):
    try:
        result = subprocess.run(cmd, capture_output=True,
                                text=True, timeout=timeout, cwd="/data")
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Comando excedió tiempo límite"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def reduce_image_resolution(image_path, reduction_percentage):
    if reduction_percentage <= 0:
        return

    img = cv2.imread(image_path)
    if img is None:
        return

    height, width = img.shape[:2]
    scale_factor = 1 - (reduction_percentage / 100)
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    if new_width > 0 and new_height > 0:
        resized_img = cv2.resize(
            img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        cv2.imwrite(image_path, resized_img)


@app.get("/photos")
async def get_photos():
    if not os.path.exists("/data/images"):
        return {
            "success": False,
            "message": "No hay fotos disponibles",
            "photos": []
        }

    photos = [f for f in os.listdir(
        "/data/images") if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'))]

    photo_info = []
    for photo in photos:
        photo_path = f"/data/images/{photo}"
        if os.path.exists(photo_path):
            file_size = os.path.getsize(photo_path)
            photo_info.append({
                "filename": photo,
                "size": file_size,
                "url": f"/photo/{photo}"
            })

    return {
        "success": True,
        "photos": photo_info,
        "total_count": len(photo_info)
    }


@app.get("/photo/{filename}")
async def get_photo(filename: str):
    file_path = f"/data/images/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Foto no encontrada")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="image/*"
    )


@app.post("/photos/select")
async def select_photos(request: PhotoSelectionRequest):
    if not os.path.exists("/data/images"):
        raise HTTPException(
            status_code=400,
            detail="No hay directorio de imágenes disponible"
        )

    all_photos = [f for f in os.listdir(
        "/data/images") if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'))]
    selected_photos = request.selected_photos
    photos_to_delete = [
        photo for photo in all_photos if photo not in selected_photos]

    deleted_count = 0
    for photo in photos_to_delete:
        photo_path = f"/data/images/{photo}"
        if os.path.exists(photo_path):
            try:
                os.remove(photo_path)
                deleted_count += 1
            except Exception as e:
                print(f"Error eliminando {photo}: {e}")

    remaining_photos = [f for f in os.listdir(
        "/data/images") if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'))]

    return {
        "success": True,
        "message": f"Selección completada. {deleted_count} fotos eliminadas.",
        "deleted_count": deleted_count,
        "remaining_count": len(remaining_photos),
        "selected_photos": selected_photos,
        "remaining_photos": remaining_photos
    }


@app.post("/photogrammetry")
async def run_photogrammetry_pipeline():
    if not os.path.exists("/data/images"):
        raise HTTPException(
            status_code=400,
            detail="Directorio /data/images no encontrado. Sube las imágenes primero."
        )

    images = [f for f in os.listdir(
        "/data/images") if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not images:
        raise HTTPException(
            status_code=400,
            detail="No se encontraron imágenes en /data/images"
        )

    pipeline_steps = []
    start_time = time.time()

    try:
        os.makedirs("/data/sparse", exist_ok=True)
        os.makedirs("/data/dense", exist_ok=True)

        step_start = time.time()
        pipeline_steps.append("1. Extrayendo características SIFT...")
        cmd = [
            "colmap", "feature_extractor",
            "--database_path", "/data/database.db",
            "--image_path", "/data/images",
            "--SiftExtraction.use_gpu", "1"
        ]
        result = run_command(cmd, timeout=600)
        print(f"Paso 1 completado en {time.time() - step_start:.2f} segundos")
        if not result["success"]:
            raise Exception(
                f"Error en extracción de características: {result.get('stderr', result.get('error'))}")

        step_start = time.time()
        pipeline_steps.append("2. Emparejando características...")
        cmd = [
            "colmap", "exhaustive_matcher",
            "--database_path", "/data/database.db",
            "--SiftMatching.use_gpu", "1"
        ]
        result = run_command(cmd, timeout=600)
        print(f"Paso 2 completado en {time.time() - step_start:.2f} segundos")
        if not result["success"]:
            raise Exception(
                f"Error en emparejamiento: {result.get('stderr', result.get('error'))}")

        step_start = time.time()
        pipeline_steps.append("3. Ejecutando reconstrucción SfM...")
        cmd = [
            "colmap", "mapper",
            "--database_path", "/data/database.db",
            "--image_path", "/data/images",
            "--output_path", "/data/sparse"
        ]
        result = run_command(cmd, timeout=1200)
        print(f"Paso 3 completado en {time.time() - step_start:.2f} segundos")
        if not result["success"]:
            raise Exception(
                f"Error en reconstrucción SfM: {result.get('stderr', result.get('error'))}")

        step_start = time.time()
        pipeline_steps.append("4. Creando imágenes sin distorsión...")
        cmd = [
            "colmap", "image_undistorter",
            "--image_path", "/data/images",
            "--input_path", "/data/sparse/0",
            "--output_path", "/data/dense",
            "--output_type", "COLMAP"
        ]
        result = run_command(cmd, timeout=600)
        print(f"Paso 4 completado en {time.time() - step_start:.2f} segundos")
        if not result["success"]:
            raise Exception(
                f"Error en undistorter: {result.get('stderr', result.get('error'))}")

        step_start = time.time()
        pipeline_steps.append("5. Convirtiendo modelo a texto...")
        cmd = [
            "colmap", "model_converter",
            "--input_path", "/data/dense/sparse",
            "--output_path", "/data/dense/sparse",
            "--output_type", "TXT"
        ]
        result = run_command(cmd, timeout=300)
        print(f"Paso 5 completado en {time.time() - step_start:.2f} segundos")
        if not result["success"]:
            raise Exception(
                f"Error en conversión: {result.get('stderr', result.get('error'))}")

        step_start = time.time()
        pipeline_steps.append("6. Convirtiendo COLMAP a MVS...")
        cmd = [
            "/usr/local/bin/OpenMVS/InterfaceCOLMAP",
            "-i", "/data/dense",
            "-o", "/data/scene.mvs",
            "--image-folder", "/data/dense/images"
        ]
        result = run_command(cmd, timeout=300)
        print(f"Paso 6 completado en {time.time() - step_start:.2f} segundos")
        if not result["success"]:
            raise Exception(
                f"Error en InterfaceCOLMAP: {result.get('stderr', result.get('error'))}")

        step_start = time.time()
        pipeline_steps.append("7. Densificando nube de puntos...")
        cmd = [
            "/usr/local/bin/OpenMVS/DensifyPointCloud",
            "-i", "/data/scene.mvs",
            "-o", "/data/scene_dense.mvs",
            "--resolution-level", "2",
        ]
        result = run_command(cmd, timeout=1800)
        print(f"Paso 7 completado en {time.time() - step_start:.2f} segundos")
        if not result["success"]:
            raise Exception(
                f"Error en densificación: {result.get('stderr', result.get('error'))}")

        step_start = time.time()
        pipeline_steps.append("8. Reconstruyendo malla...")
        cmd = [
            "/usr/local/bin/OpenMVS/ReconstructMesh",
            "-i", "/data/scene_dense.mvs",
            "-o", "/data/scene_mesh.mvs",
            "--max-threads", "24",
            "--decimate", "0.4",
            "--target-face-num", "100000",
        ]
        result = run_command(cmd, timeout=100)
        print(f"Paso 8 completado en {time.time() - step_start:.2f} segundos")
        if not result["success"]:
            raise Exception(
                f"Error en reconstrucción de malla: {result.get('stderr', result.get('error'))}")

        step_start = time.time()
        pipeline_steps.append("9. Texturizando malla...")
        cmd = [
            "/usr/local/bin/OpenMVS/TextureMesh",
            "/data/scene_dense.mvs",
            "-m", "/data/scene_mesh.ply",
            "-o", "/data/scene_textured.mvs",
            "--export-type", "obj",
            "--resolution-level", "1",
            "--max-threads", "24",
        ]
        result = run_command(cmd, timeout=60)
        print(f"Paso 9 completado en {time.time() - step_start:.2f} segundos")
        if not result["success"]:
            raise Exception(
                f"Error en texturización: {result.get('stderr', result.get('error'))}")

        files_to_compress = []
        required_files = ["scene_textured.obj", "scene_textured.mtl"]
        for file in required_files:
            if os.path.exists(f"/data/{file}"):
                files_to_compress.append(file)

        texture_files = [f for f in os.listdir(
            "/data") if f.lower().endswith(('.jpg', '.jpeg', '.png')) and 'texture' in f.lower()]
        files_to_compress.extend(texture_files)

        zip_filename = "/data/photogrammetry_result.zip"
        if files_to_compress:
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files_to_compress:
                    file_path = f"/data/{file}"
                    if os.path.exists(file_path):
                        zipf.write(file_path, file)
            zip_size = os.path.getsize(zip_filename)
        else:
            zip_size = 0

        mesh_stats = extract_mesh_statistics("/data/scene_textured.obj")
        texture_info = get_texture_files_info("/data")

        pipeline_steps.append("10. Limpiando archivos temporales...")
        files_to_keep = ["images", "photogrammetry_result.zip"]
        for item in os.listdir("/data"):
            item_path = f"/data/{item}"
            if item not in files_to_keep:
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"Error eliminando {item}: {e}")

        total_time = time.time() - start_time
        print(f"Pipeline completo en {total_time:.2f} segundos")

        return {
            "success": True,
            "message": "Pipeline de fotogrametría completado exitosamente",
            "download_ready": True,
            "download_url": "/download/photogrammetry_result.zip",
            "steps_completed": pipeline_steps,
            "images_processed": len(images),
            "zip_file": {
                "filename": "photogrammetry_result.zip",
                "size_bytes": zip_size,
                "contains": files_to_compress
            },
            "mesh_statistics": mesh_stats,  # NUEVO
            "texture_info": texture_info,   # NUEVO
            "files_cleaned": True,
            "execution_time_seconds": round(total_time, 2)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "steps_completed": pipeline_steps,
                "message": "Pipeline falló durante la ejecución",
                "error_details": {
                    "message": str(e),
                    "traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else "No traceback available"
                }
            }
        )


@app.post("/extractframes")
async def extract_frames_from_video(video: UploadFile = File(...), num_frames: int = 60, segment_objects: bool = False):
    os.makedirs("/data", exist_ok=True)

    video_path = f"/data/{video.filename}"
    with open(video_path, "wb") as buffer:
        content = await video.read()
        buffer.write(content)

    if os.path.exists("/data/images"):
        shutil.rmtree("/data/images")
    if os.path.exists("/data/images_segmented"):
        shutil.rmtree("/data/images_segmented")
    if os.path.exists("/data/images_masks"):
        shutil.rmtree("/data/images_masks")

    try:
        extracted_frames = extract_frames_smart(
            video_path, "/data/frames_temp", target_frames=num_frames, debug=False)

        if not extracted_frames:
            raise HTTPException(
                status_code=400,
                detail="No se pudieron extraer frames del video"
            )

        os.remove(video_path)

        if segment_objects:
            try:
                from utils.segmentImages import segment_images_for_photogrammetry
                segmented_paths, mask_paths = segment_images_for_photogrammetry(
                    input_folder="/data/frames_temp",
                    output_folder_segmented="/data/images_segmented",
                    output_folder_mask="/data/images_masks",
                    model_path="/app/models/yolo11l-seg.pt",
                    confidence=0.3,
                    max_workers=1,
                    min_area_ratio=0.08,
                    use_adaptive_confidence=True,
                    prefer_centered_objects=True
                )

                if segmented_paths:
                    os.rename("/data/images_segmented", "/data/images")
                    shutil.rmtree("/data/frames_temp")
                    if os.path.exists("/data/images_masks"):
                        shutil.rmtree("/data/images_masks")

                    segmentation_info = {
                        "segmented": True,
                        "segmented_images": len(segmented_paths),
                        "original_frames": len(extracted_frames)
                    }
                else:
                    os.rename("/data/frames_temp", "/data/images")
                    segmentation_info = {
                        "segmented": False,
                        "reason": "No se pudieron segmentar objetos válidos",
                        "fallback_to_original": True
                    }
            except Exception as seg_error:
                os.rename("/data/frames_temp", "/data/images")
                segmentation_info = {
                    "segmented": False,
                    "error": str(seg_error),
                    "fallback_to_original": True
                }
        else:
            os.rename("/data/frames_temp", "/data/images")
            segmentation_info = {
                "segmented": False,
                "reason": "Segmentación deshabilitada por parámetro"
            }

        images = [f for f in os.listdir(
            "/data/images") if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        return {
            "success": True,
            "message": "Frames extraídos exitosamente",
            "frames_extracted": len(extracted_frames),
            "segmentation_info": segmentation_info,
            "images_processed": len(images),
            "output_folder": "/data/images"
        }

    except Exception as e:
        if os.path.exists(video_path):
            os.remove(video_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error extrayendo frames: {str(e)}"
        )


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"/data/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/zip"
    )


@app.post("/uploadphotos")
async def upload_photos_from_zip(photos_zip: UploadFile = File(...), segment_objects: bool = False, reduction_percentage: int = 0):
    if not photos_zip.filename.lower().endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un ZIP"
        )

    os.makedirs("/data", exist_ok=True)

    if os.path.exists("/data/images"):
        shutil.rmtree("/data/images")
    if os.path.exists("/data/images_segmented"):
        shutil.rmtree("/data/images_segmented")
    if os.path.exists("/data/images_masks"):
        shutil.rmtree("/data/images_masks")

    zip_path = f"/data/{photos_zip.filename}"
    with open(zip_path, "wb") as buffer:
        content = await photos_zip.read()
        buffer.write(content)

    try:
        temp_extract_folder = "/data/photos_temp"
        os.makedirs(temp_extract_folder, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_folder)

        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
        extracted_images = []

        for root, dirs, files in os.walk(temp_extract_folder):
            for file in files:
                if file.lower().endswith(valid_extensions):
                    extracted_images.append(os.path.join(root, file))

        if not extracted_images:
            raise HTTPException(
                status_code=400,
                detail="No se encontraron imágenes válidas en el ZIP"
            )

        os.makedirs("/data/images", exist_ok=True)

        copied_images = []
        for i, img_path in enumerate(extracted_images):
            _, ext = os.path.splitext(img_path)
            new_name = f"image_{i+1:04d}{ext}"
            dest_path = f"/data/images/{new_name}"
            shutil.copy2(img_path, dest_path)
            copied_images.append(new_name)

        os.remove(zip_path)
        shutil.rmtree(temp_extract_folder)

        if reduction_percentage > 0:
            for img_file in copied_images:
                img_path = os.path.join("/data/images", img_file)
                reduce_image_resolution(img_path, reduction_percentage)

        if segment_objects:
            try:
                # from utils.segmentImages import segment_images_for_photogrammetry
                # segmented_paths, mask_paths = segment_images_for_photogrammetry(
                #     input_folder="/data/images",
                #     output_folder_segmented="/data/images_segmented",
                #     output_folder_mask="/data/images_masks",
                #     model_path="/app/models/yolo11l-seg.pt",
                #     confidence=0.2,
                #     max_workers=1,
                #     min_area_ratio=0.08,
                #     use_adaptive_confidence=True,
                #     prefer_centered_objects=True
                # )
                from utils.segmentImages import segment_images_for_photogrammetry_improved
                segmented_paths, mask_paths = segment_images_for_photogrammetry_improved(
                    input_folder="/data/images",
                    output_folder_segmented="/data/images_segmented",
                    output_folder_mask="/data/images_masks",
                    model_path="/app/models/yolo11l-seg.pt",
                )

                if segmented_paths:
                    shutil.rmtree("/data/images")
                    os.rename("/data/images_segmented", "/data/images")
                    if os.path.exists("/data/images_masks"):
                        shutil.rmtree("/data/images_masks")

                    segmentation_info = {
                        "segmented": True,
                        "segmented_images": len(segmented_paths),
                        "original_images": len(copied_images)
                    }
                else:
                    segmentation_info = {
                        "segmented": False,
                        "reason": "No se pudieron segmentar objetos válidos",
                        "fallback_to_original": True
                    }
            except Exception as seg_error:
                segmentation_info = {
                    "segmented": False,
                    "error": str(seg_error),
                    "fallback_to_original": True
                }
        else:
            segmentation_info = {
                "segmented": False,
                "reason": "Segmentación deshabilitada por parámetro"
            }

        final_images = [f for f in os.listdir("/data/images")
                        if f.lower().endswith(valid_extensions)]

        return {
            "success": True,
            "message": "Fotos subidas exitosamente",
            "images_uploaded": len(copied_images),
            "segmentation_info": segmentation_info,
            "images_processed": len(final_images),
            "reduction_percentage": reduction_percentage,
            "output_folder": "/data/images",
            "supported_formats": list(valid_extensions)
        }

    except zipfile.BadZipFile:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise HTTPException(
            status_code=400,
            detail="El archivo no es un ZIP válido"
        )
    except Exception as e:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists("/data/photos_temp"):
            shutil.rmtree("/data/photos_temp")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando el ZIP: {str(e)}"
        )
