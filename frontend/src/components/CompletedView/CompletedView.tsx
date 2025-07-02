import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, Download, Box, Image, FileText, Zap } from 'lucide-react'

interface MeshStats {
    vertices: number
    faces: number
    triangles: number
    texture_coordinates: number
    vertex_normals: number
    file_size_mb: number
}

interface TextureInfo {
    texture_files: Array<{
        filename: string
        size_mb: number
        resolution?: string
    }>
    total_textures: number
    total_texture_size_mb: number
}

interface CompletedViewProps {
    message: string
    meshStats?: MeshStats | null
    textureInfo?: TextureInfo | null
    onDownload: () => void
    onReset: () => void
}

export function CompletedView({
    message,
    meshStats,
    textureInfo,
    onDownload,
    onReset
}: CompletedViewProps) {
    const formatNumber = (num: number) => {
        return new Intl.NumberFormat('es-ES').format(num)
    }

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
            <div className="w-full max-w-2xl space-y-6">
                {/* Main Success Card */}
                <Card>
                    <CardHeader className="text-center">
                        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <CheckCircle className="w-8 h-8 text-green-600" />
                        </div>
                        <CardTitle className="text-2xl">¡Modelo 3D Completado!</CardTitle>
                        <CardDescription>{message}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <Button onClick={onDownload} className="w-full" size="lg">
                            <Download className="w-4 h-4 mr-2" />
                            Descargar Modelo 3D
                        </Button>
                        <Button onClick={onReset} variant="outline" className="w-full">
                            Crear Nuevo Modelo
                        </Button>
                    </CardContent>
                </Card>

                {/* Mesh Statistics */}
                {meshStats && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-lg">
                                <Box className="w-5 h-5 text-blue-600" />
                                Estadísticas del Modelo
                            </CardTitle>
                            <CardDescription>
                                Detalles técnicos de tu modelo 3D generado
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                                    <div className="text-2xl font-bold text-blue-700">
                                        {formatNumber(meshStats.vertices)}
                                    </div>
                                    <div className="text-sm text-blue-600">Vértices</div>
                                </div>

                                <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                                    <div className="text-2xl font-bold text-purple-700">
                                        {formatNumber(meshStats.triangles)}
                                    </div>
                                    <div className="text-sm text-purple-600">Triángulos</div>
                                </div>

                                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                                    <div className="text-2xl font-bold text-green-700">
                                        {meshStats.file_size_mb} MB
                                    </div>
                                    <div className="text-sm text-green-600">Tamaño</div>
                                </div>

                                <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                                    <div className="text-2xl font-bold text-orange-700">
                                        {formatNumber(meshStats.faces)}
                                    </div>
                                    <div className="text-sm text-orange-600">Caras</div>
                                </div>

                                <div className="bg-teal-50 p-4 rounded-lg border border-teal-200">
                                    <div className="text-2xl font-bold text-teal-700">
                                        {formatNumber(meshStats.texture_coordinates)}
                                    </div>
                                    <div className="text-sm text-teal-600">Coords. UV</div>
                                </div>

                                <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
                                    <div className="text-2xl font-bold text-indigo-700">
                                        {formatNumber(meshStats.vertex_normals)}
                                    </div>
                                    <div className="text-sm text-indigo-600">Normales</div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Texture Information */}
                {textureInfo && textureInfo.total_textures > 0 && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-lg">
                                <Image className="w-5 h-5 text-green-600" />
                                Información de Texturas
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-gray-600">Total de texturas:</span>
                                    <Badge variant="secondary">
                                        {textureInfo.total_textures} archivo{textureInfo.total_textures > 1 ? 's' : ''}
                                    </Badge>
                                </div>

                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-gray-600">Tamaño total:</span>
                                    <Badge variant="outline">
                                        {textureInfo.total_texture_size_mb} MB
                                    </Badge>
                                </div>

                                {textureInfo.texture_files.map((texture, index) => (
                                    <div key={index} className="bg-gray-50 p-3 rounded-lg">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <FileText className="w-4 h-4 text-gray-500" />
                                                <span className="text-sm font-medium">{texture.filename}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {texture.resolution && (
                                                    <Badge variant="outline" className="text-xs">
                                                        {texture.resolution}
                                                    </Badge>
                                                )}
                                                <Badge variant="secondary" className="text-xs">
                                                    {texture.size_mb} MB
                                                </Badge>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Quality Indicator */}
                {meshStats && (
                    <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-center gap-3">
                                <Zap className="w-5 h-5 text-blue-600" />
                                <span className="font-medium text-blue-800">
                                    Modelo de {meshStats.vertices > 50000 ? 'Alta' : meshStats.vertices > 20000 ? 'Media' : 'Baja'} Resolución
                                </span>
                                <Badge variant="outline" className="border-blue-300 text-blue-700">
                                    {meshStats.vertices > 50000 ? 'Excelente' : meshStats.vertices > 20000 ? 'Buena' : 'Básica'} Calidad
                                </Badge>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    )
}