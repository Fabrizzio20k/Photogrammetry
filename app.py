import time
import subprocess
import os
import zipfile
import shutil
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from utils.extractPhotosFromVideo import extract_frames_smart
from utils.segmentImages import segment_images_for_photogrammetry
from fastapi.responses import FileResponse

app = FastAPI()


def run_command(cmd, timeout=300):
    """Ejecutar comando y retornar resultado"""
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


@app.post("/photogrammetry")
async def run_photogrammetry_pipeline():
    """Ejecutar el pipeline completo de fotogrametría"""

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
            # Reducir malla al 50% (default: 1 = sin reducción)
            "--decimate", "0.5",
            "--target-face-num", "100000",
        ]
        result = run_command(cmd, timeout=60)
        print(f"Paso 8 completado en {time.time() - step_start:.2f} segundos")
        if not result["success"]:
            raise Exception(
                f"Error en reconstrucción de malla: {result.get('stderr', result.get('error'))}")

        # Paso 9: TextureMesh CORREGIDO Y OPTIMIZADO
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
        # 1 minuto de timeout para texturización
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


@app.post("/uploadPhotos")
async def upload_photos(zip_file: UploadFile = File(...)):
    """Sube un archivo ZIP con fotos y las guarda en /data/images"""

    if not zip_file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400, detail="El archivo debe ser un .zip que contenga imágenes")
    try:
        if os.path.exists("/data"):
            shutil.rmtree("/data")
        os.makedirs("/data/images", exist_ok=True)

        zip_path = f"/data/{zip_file.filename}"
        with open(zip_path, "wb") as f:
            content = await zip_file.read()
            f.write(content)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("/data/images")

        os.remove(zip_path)

        extracted_files = os.listdir("/data/images")
        image_files = [
            f for f in extracted_files
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ]

        if not image_files:
            raise HTTPException(
                status_code=400,
                detail="El archivo .zip no contiene imágenes válidas (.jpg, .jpeg, .png)"
            )

        return {
            "success": True,
            "message": "Fotos subidas y extraídas exitosamente",
            "total_files": len(extracted_files),
            "image_files_count": len(image_files),
            "image_filenames": image_files
        }

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail="El archivo no es un ZIP válido"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando el archivo: {str(e)}"
        )
