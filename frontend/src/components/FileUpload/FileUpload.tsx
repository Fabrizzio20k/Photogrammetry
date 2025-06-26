import { useDropzone } from 'react-dropzone'
import { Upload, Video, Image as ImageIcon, FileText, Play, Loader2, X } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Mode, ProcessStep, Config } from '@/types/photogrammetry'

interface FileUploadProps {
    mode: Mode
    step: ProcessStep
    uploadedFile: File | null
    config: Config
    progress: number
    message: string
    onModeChange: () => void
    onFileUpload: (file: File) => void
    onConfigChange: (config: Config) => void
    onFileRemove: () => void
    onProcess: () => void
}

export function FileUpload({
    mode,
    step,
    uploadedFile,
    config,
    progress,
    message,
    onModeChange,
    onFileUpload,
    onConfigChange,
    onFileRemove,
    onProcess
}: FileUploadProps) {
    const onDrop = (acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            onFileUpload(acceptedFiles[0])
        }
    }

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: mode === 'video'
            ? { 'video/*': ['.mp4', '.avi', '.mov'] }
            : { 'application/zip': ['.zip'] },
        maxFiles: 1
    })

    return (
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
                    <Button variant="outline" onClick={onModeChange}>
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
                                        onValueChange={([value]) => onConfigChange({
                                            ...config,
                                            numFrames: value
                                        })}
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
                                    onValueChange={([value]) => onConfigChange({
                                        ...config,
                                        reductionPercentage: value
                                    })}
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
                                    onCheckedChange={(checked) => onConfigChange({
                                        ...config,
                                        segmentObjects: checked
                                    })}
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
                                    onClick={() => {
                                        onFileRemove()
                                    }}
                                    className="flex-1"
                                    disabled={step !== 'idle'}
                                >
                                    <X className="w-4 h-4 mr-2" />
                                    Quitar archivo
                                </Button>
                                <Button
                                    onClick={onProcess}
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
    )
}
