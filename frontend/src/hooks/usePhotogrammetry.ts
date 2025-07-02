import { useState } from 'react'
import { Mode, ProcessStep, Photo, Config } from '../types/photogrammetry'

export function usePhotogrammetry() {
    const [mode, setMode] = useState<Mode>(null)
    const [step, setStep] = useState<ProcessStep>('idle')
    const [uploadedFile, setUploadedFile] = useState<File | null>(null)
    const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
    const [message, setMessage] = useState('')
    const [progress, setProgress] = useState(0)
    const [photos, setPhotos] = useState<Photo[]>([])
    const [selectedPhotos, setSelectedPhotos] = useState<Set<string>>(new Set())
    const [showPhotoSelection, setShowPhotoSelection] = useState(false)
    const [meshStats, setMeshStats] = useState(null)
    const [textureInfo, setTextureInfo] = useState(null)
    const [config, setConfig] = useState<Config>({
        numFrames: 60,
        segmentObjects: false,
        reductionPercentage: 0
    })

    const fetchPhotos = async () => {
        try {
            const response = await fetch('http://localhost:8000/photos')
            if (response.ok) {
                const result = await response.json()
                if (result.success) {
                    setPhotos(result.photos)
                    setSelectedPhotos(new Set(result.photos.map((p: Photo) => p.filename)))
                }
            }
        } catch (error) {
            console.error('Error fetching photos:', error)
        }
    }

    const processFile = async () => {
        if (!uploadedFile) return

        setStep('uploading')
        setMessage('Subiendo archivo...')
        setProgress(20)

        try {
            const formData = new FormData()

            if (mode === 'video') {
                formData.append('video', uploadedFile)
                const url = new URL('http://localhost:8000/extractframes')
                url.searchParams.append('num_frames', config.numFrames.toString())
                url.searchParams.append('segment_objects', config.segmentObjects.toString())
                url.searchParams.append('reduction_percentage', config.reductionPercentage.toString())

                setStep('processing')
                setMessage('Extrayendo frames del video...')
                setProgress(50)

                const response = await fetch(url.toString(), {
                    method: 'POST',
                    body: formData
                })

                if (!response.ok) {
                    const errorData = await response.json()
                    throw new Error(errorData.detail || 'Error al procesar video')
                }

                const result = await response.json()
                setProgress(80)
                setMessage(`Video procesado exitosamente. ${result.images_processed} imágenes extraídas.`)
            } else {
                formData.append('photos_zip', uploadedFile)
                const url = new URL('http://localhost:8000/uploadphotos')
                url.searchParams.append('segment_objects', config.segmentObjects.toString())
                url.searchParams.append('reduction_percentage', config.reductionPercentage.toString())

                setStep('processing')
                setMessage('Procesando archivo ZIP...')
                setProgress(50)

                const response = await fetch(url.toString(), {
                    method: 'POST',
                    body: formData
                })

                if (!response.ok) {
                    const errorData = await response.json()
                    throw new Error(errorData.detail || 'Error al procesar ZIP')
                }

                const result = await response.json()
                setProgress(80)
                setMessage(`ZIP procesado exitosamente. ${result.images_processed} imágenes cargadas.`)
            }

            setProgress(100)
            await fetchPhotos()

            setTimeout(() => {
                setStep('idle')
                setProgress(0)
                setMessage('Archivo procesado exitosamente. Selecciona las fotos que deseas usar.')
                setShowPhotoSelection(true)
            }, 1000)

        } catch (error) {
            console.error('Error:', error)
            setMessage(`Error: ${error instanceof Error ? error.message : 'Error desconocido'}`)
            setStep('idle')
            setProgress(0)
        }
    }

    const runPhotogrammetry = async () => {
        setStep('photogrammetry')
        setMessage('Ejecutando pipeline de fotogrametría...')
        setProgress(0)

        const progressInterval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 90) return prev
                return prev + Math.random() * 10
            })
        }, 2000)

        try {
            const response = await fetch('http://localhost:8000/photogrammetry', {
                method: 'POST'
            })

            if (response.ok) {
                const result = await response.json()

                if (result.success) {
                    clearInterval(progressInterval)
                    setProgress(100)
                    setDownloadUrl(result.download_url)

                    // Guardar estadísticas del mesh
                    if (result.mesh_statistics) {
                        setMeshStats(result.mesh_statistics)
                    }
                    if (result.texture_info) {
                        setTextureInfo(result.texture_info)
                    }

                    setStep('completed')
                    setMessage('¡Proceso completado! Tu modelo 3D está listo para descargar.')
                } else {
                    throw new Error(result.error || 'Error en fotogrametría')
                }
            } else {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Error en fotogrametría')
            }
        } catch (error) {
            console.error('Error:', error)
            clearInterval(progressInterval)
            setMessage(`Error en fotogrametría: ${error instanceof Error ? error.message : 'Error desconocido'}`)
            setStep('idle')
            setProgress(0)
        }
    }

    const confirmPhotoSelection = async () => {
        try {
            const response = await fetch('http://localhost:8000/photos/select', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    selected_photos: Array.from(selectedPhotos)
                })
            })

            if (response.ok) {
                const result = await response.json()
                setMessage(`Selección confirmada. ${result.remaining_count} fotos listas para fotogrametría.`)
                setShowPhotoSelection(false)
                setStep('idle')
                await fetchPhotos()
            } else {
                throw new Error('Error al confirmar selección')
            }
        } catch (error) {
            console.error('Error confirming selection:', error)
            setMessage('Error al confirmar la selección de fotos')
        }
    }

    const reset = () => {
        setMode(null)
        setStep('idle')
        setUploadedFile(null)
        setDownloadUrl(null)
        setMessage('')
        setProgress(0)
        setPhotos([])
        setSelectedPhotos(new Set())
        setShowPhotoSelection(false)
        setMeshStats(null)
        setTextureInfo(null)
        setConfig({
            numFrames: 60,
            segmentObjects: false,
            reductionPercentage: 0
        })
    }

    return {
        // Estado
        mode,
        step,
        uploadedFile,
        downloadUrl,
        message,
        progress,
        photos,
        selectedPhotos,
        showPhotoSelection,
        config,
        meshStats,
        textureInfo,
        // Acciones
        setMode,
        setUploadedFile,
        setMessage,
        setSelectedPhotos,
        setShowPhotoSelection,
        setConfig,
        processFile,
        runPhotogrammetry,
        confirmPhotoSelection,
        reset,
        downloadResult: () => downloadUrl && window.open(`http://localhost:8000${downloadUrl}`, '_blank')
    }
}