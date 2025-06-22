'use client'

import React, { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Video, Image as ImageIcon, Download, Play, Loader2, CheckCircle, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'

type Mode = 'photos' | 'video' | null
type ProcessStep = 'idle' | 'uploading' | 'processing' | 'photogrammetry' | 'completed'

export default function PhotogrammetryInterface() {
    const [mode, setMode] = useState<Mode>(null)
    const [step, setStep] = useState<ProcessStep>('idle')
    const [uploadedFile, setUploadedFile] = useState<File | null>(null)
    const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
    const [message, setMessage] = useState('')
    const [progress, setProgress] = useState(0)

    const [config, setConfig] = useState({
        numFrames: 60,
        segmentObjects: false,
        reductionPercentage: 0
    })

    const onDrop = (acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            setUploadedFile(acceptedFiles[0])
            setMessage('')
        }
    }

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: mode === 'video'
            ? { 'video/*': ['.mp4', '.avi', '.mov'] }
            : { 'application/zip': ['.zip'] },
        maxFiles: 1
    })

    const processFile = async () => {
        if (!uploadedFile) return

        setStep('uploading')
        setMessage('Subiendo archivo...')
        setProgress(20)

        try {
            const formData = new FormData()

            if (mode === 'video') {
                formData.append('video', uploadedFile)

                // Construir URL con query parameters
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
                console.log('Video processing result:', result)

                setProgress(80)
                setMessage(`Video procesado exitosamente. ${result.images_processed} imágenes listas.`)

            } else {
                formData.append('photos_zip', uploadedFile)

                // Construir URL con query parameters
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
                console.log('Photos processing result:', result)

                setProgress(80)
                setMessage(`ZIP procesado exitosamente. ${result.images_processed} imágenes listas.`)
            }

            setProgress(100)
            setTimeout(() => {
                setStep('idle')
                setProgress(0)
                setMessage('Archivo procesado exitosamente. Listo para iniciar fotogrametría.')
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
                console.log('Photogrammetry result:', result)

                if (result.success) {
                    clearInterval(progressInterval)
                    setProgress(100)
                    setDownloadUrl(result.download_url)
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

    const downloadResult = () => {
        if (downloadUrl) {
            window.open(`http://localhost:8000${downloadUrl}`, '_blank')
        }
    }

    const reset = () => {
        setMode(null)
        setStep('idle')
        setUploadedFile(null)
        setDownloadUrl(null)
        setMessage('')
        setProgress(0)
        setConfig({
            numFrames: 60,
            segmentObjects: false,
            reductionPercentage: 0
        })
    }

    if (step === 'completed') {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <CheckCircle className="w-8 h-8 text-green-600" />
                        </div>
                        <CardTitle className="text-2xl">¡Completado!</CardTitle>
                        <CardDescription>{message}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <Button onClick={downloadResult} className="w-full" size="lg">
                            <Download className="w-4 h-4 mr-2" />
                            Descargar Resultado
                        </Button>
                        <Button onClick={reset} variant="outline" className="w-full">
                            Nuevo Proyecto
                        </Button>
                    </CardContent>
                </Card>
            </div>
        )
    }

    if (step === 'photogrammetry') {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <Loader2 className="w-16 h-16 text-blue-600 animate-spin mx-auto mb-4" />
                        <CardTitle className="text-2xl">Procesando Fotogrametría</CardTitle>
                        <CardDescription>Esto puede tomar varios minutos...</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <Progress value={progress} className="w-full" />
                            <p className="text-sm text-center text-gray-600">{Math.round(progress)}% completado</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="container mx-auto p-6 max-w-4xl">
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">Fotogrametría 3D</h1>
                    <p className="text-lg text-gray-600">Convierte fotos o videos en modelos 3D</p>
                </div>

                {!mode ? (
                    <div className="grid md:grid-cols-2 gap-6 mb-8">
                        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setMode('photos')}>
                            <CardHeader>
                                <ImageIcon className="w-12 h-12 text-green-600 mb-4" />
                                <CardTitle>Subir Fotos</CardTitle>
                                <CardDescription>
                                    Archivo ZIP con múltiples fotografías del objeto a reconstruir
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <Badge variant="secondary">ZIP con imágenes</Badge>
                            </CardContent>
                        </Card>

                        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setMode('video')}>
                            <CardHeader>
                                <Video className="w-12 h-12 text-blue-600 mb-4" />
                                <CardTitle>Subir Video</CardTitle>
                                <CardDescription>
                                    Video del objeto para extraer frames automáticamente
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <Badge variant="secondary">MP4, AVI, MOV</Badge>
                            </CardContent>
                        </Card>
                    </div>
                ) : (
                    <Card className="mb-6">
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    {mode === 'video' ? (
                                        <Video className="w-8 h-8 text-blue-600" />
                                    ) : (
                                        <ImageIcon className="w-8 h-8 text-green-600" />
                                    )}
                                    <div>
                                        <CardTitle>
                                            {mode === 'video' ? 'Subir Video' : 'Subir Fotos (ZIP)'}
                                        </CardTitle>
                                        <CardDescription>
                                            {mode === 'video'
                                                ? 'Formatos soportados: MP4, AVI, MOV'
                                                : 'Archivo ZIP con imágenes JPG/PNG'
                                            }
                                        </CardDescription>
                                    </div>
                                </div>
                                <Button variant="outline" onClick={() => setMode(null)}>
                                    Cambiar
                                </Button>
                            </div>
                        </CardHeader>

                        <CardContent>
                            {!uploadedFile ? (
                                <div
                                    {...getRootProps()}
                                    className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragActive
                                        ? 'border-blue-500 bg-blue-50'
                                        : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                                        }`}
                                >
                                    <input {...getInputProps()} />
                                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                                    <div className="space-y-2">
                                        <p className="text-lg font-medium text-gray-900">
                                            {isDragActive
                                                ? 'Suelta el archivo aquí...'
                                                : 'Arrastra un archivo o haz clic para seleccionar'
                                            }
                                        </p>
                                        <p className="text-sm text-gray-500">
                                            {mode === 'video'
                                                ? 'Formatos: MP4, AVI, MOV (máx. 100MB)'
                                                : 'Formato: ZIP con imágenes (máx. 50MB)'
                                            }
                                        </p>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    <Card className="bg-gray-50">
                                        <CardContent className="pt-4">
                                            <div className="flex items-center gap-3">
                                                <FileText className="w-8 h-8 text-gray-600" />
                                                <div>
                                                    <p className="font-medium text-gray-900">{uploadedFile.name}</p>
                                                    <p className="text-sm text-gray-500">
                                                        {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                                                    </p>
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>

                                    <div className="grid gap-6">
                                        {mode === 'video' && (
                                            <div className="space-y-3">
                                                <Label htmlFor="frames">Número de Frames: {config.numFrames}</Label>
                                                <Slider
                                                    id="frames"
                                                    min={20}
                                                    max={200}
                                                    step={10}
                                                    value={[config.numFrames]}
                                                    onValueChange={([value]) => setConfig(prev => ({
                                                        ...prev,
                                                        numFrames: value
                                                    }))}
                                                    className="w-full"
                                                />
                                                <div className="flex justify-between text-xs text-gray-500">
                                                    <span>20 frames</span>
                                                    <span>200 frames</span>
                                                </div>
                                            </div>
                                        )}

                                        <div className="space-y-3">
                                            <Label htmlFor="reduction">Reducción de Resolución: {config.reductionPercentage}%</Label>
                                            <Slider
                                                id="reduction"
                                                min={0}
                                                max={70}
                                                step={10}
                                                value={[config.reductionPercentage]}
                                                onValueChange={([value]) => setConfig(prev => ({
                                                    ...prev,
                                                    reductionPercentage: value
                                                }))}
                                                className="w-full"
                                            />
                                            <div className="flex justify-between text-xs text-gray-500">
                                                <span>Sin reducción</span>
                                                <span>Máxima reducción</span>
                                            </div>
                                        </div>

                                        <div className="flex items-center space-x-3">
                                            <Switch
                                                id="segmentation"
                                                checked={config.segmentObjects}
                                                onCheckedChange={(checked) => setConfig(prev => ({
                                                    ...prev,
                                                    segmentObjects: checked
                                                }))}
                                            />
                                            <Label htmlFor="segmentation" className="text-sm font-medium">
                                                Activar segmentación de objetos
                                            </Label>
                                            {config.segmentObjects && (
                                                <Badge variant="outline" className="text-xs">
                                                    Experimental
                                                </Badge>
                                            )}
                                        </div>

                                        {(step === 'uploading' || step === 'processing') && (
                                            <div className="space-y-2">
                                                <Progress value={progress} className="w-full" />
                                                <p className="text-sm text-center text-gray-600">{message}</p>
                                            </div>
                                        )}

                                        <div className="flex gap-3">
                                            <Button
                                                variant="outline"
                                                onClick={() => setUploadedFile(null)}
                                                className="flex-1"
                                                disabled={step !== 'idle'}
                                            >
                                                Cancelar
                                            </Button>
                                            <Button
                                                onClick={processFile}
                                                disabled={step !== 'idle'}
                                                className="flex-1"
                                            >
                                                {step === 'uploading' || step === 'processing' ? (
                                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                                ) : (
                                                    <Play className="w-4 h-4 mr-2" />
                                                )}
                                                Procesar
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {message && step === 'idle' && uploadedFile && (
                    <Card>
                        <CardContent className="pt-6">
                            <div className="text-center space-y-4">
                                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                                    <CheckCircle className="w-6 h-6 text-green-600" />
                                </div>
                                <p className="text-gray-900 font-medium">{message}</p>
                                <Button onClick={runPhotogrammetry} size="lg" className="min-w-[200px]">
                                    <Play className="w-4 h-4 mr-2" />
                                    Iniciar Fotogrametría
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    )
}