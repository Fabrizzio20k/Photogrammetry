import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Eye, X, CheckCircle, Trash2 } from 'lucide-react'
import Image from 'next/image'
import { useState, useEffect } from 'react'
import { Photo } from '@/types/photogrammetry'

interface PhotoSelectorProps {
    photos: Photo[]
    selectedPhotos: Set<string>
    onToggleSelection: (filename: string) => void
    onSelectAll: () => void
    onDeselectAll: () => void
    onConfirm: () => void
    onClose: () => void
}

export function PhotoSelector({
    photos,
    selectedPhotos,
    onToggleSelection,
    onSelectAll,
    onDeselectAll,
    onConfirm,
    onClose
}: PhotoSelectorProps) {
    const [imageTimestamp, setImageTimestamp] = useState(Date.now())

    // Solo actualizar timestamp cuando cambia el array de fotos
    useEffect(() => {
        setImageTimestamp(Date.now())
    }, [photos.length])

    return (
        <Card className="mb-6">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <Eye className="w-5 h-5" />
                            Seleccionar Fotos
                        </CardTitle>
                        <CardDescription>
                            Marca las fotos que deseas usar para la fotogrametría. {selectedPhotos.size} de {photos.length} seleccionadas.
                        </CardDescription>
                    </div>
                    <Button variant="outline" size="sm" onClick={onClose}>
                        <X className="w-4 h-4" />
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 mb-6">
                    {photos.map((photo, index) => (
                        <div
                            key={`${photo.filename}-${index}`}
                            className={`relative group cursor-pointer border-2 rounded-lg overflow-hidden transition-all ${selectedPhotos.has(photo.filename)
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                                }`}
                            onClick={() => onToggleSelection(photo.filename)}
                        >
                            <div className="aspect-square relative bg-gray-100">
                                <Image
                                    src={`http://localhost:8000${photo.url}?t=${imageTimestamp}`}
                                    alt={photo.filename}
                                    fill
                                    className="object-cover z-10 inset-0"
                                    unoptimized={true}
                                    priority={index < 10}
                                />

                                <div className={`absolute top-2 right-2 w-6 h-6 rounded-full border-2 flex items-center justify-center z-10 transition-all ${selectedPhotos.has(photo.filename)
                                    ? 'bg-blue-500 border-blue-500'
                                    : 'bg-white border-gray-300 group-hover:border-gray-400'
                                    }`}>
                                    {selectedPhotos.has(photo.filename) && (
                                        <CheckCircle className="w-4 h-4 text-white" />
                                    )}
                                </div>

                                {!selectedPhotos.has(photo.filename) && (
                                    <div className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                        <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                                            <Trash2 className="w-3 h-3 text-white" />
                                        </div>
                                    </div>
                                )}

                                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all" />
                            </div>

                            <div className="p-2">
                                <p className="text-xs text-gray-600 truncate">{photo.filename}</p>
                                <p className="text-xs text-gray-500">{(photo.size / 1024).toFixed(1)} KB</p>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="flex gap-3">
                    <Button
                        variant="outline"
                        onClick={onDeselectAll}
                        disabled={selectedPhotos.size === 0}
                    >
                        Deseleccionar todo
                    </Button>
                    <Button
                        variant="outline"
                        onClick={onSelectAll}
                        disabled={selectedPhotos.size === photos.length}
                    >
                        Seleccionar todo
                    </Button>
                    <Button
                        onClick={onConfirm}
                        disabled={selectedPhotos.size === 0}
                        className="ml-auto"
                    >
                        Confirmar Selección ({selectedPhotos.size})
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
