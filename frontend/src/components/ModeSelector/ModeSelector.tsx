// components/ModeSelector.tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Video, Image as ImageIcon, Upload, Zap, Camera, Film, ArrowRight } from 'lucide-react'
import { Mode } from '@/types/photogrammetry'

interface ModeSelectorProps {
    onModeSelect: (mode: Mode) => void
}

export function ModeSelector({ onModeSelect }: ModeSelectorProps) {
    return (
        <div className="space-y-12">
            {/* Hero Section */}
            <div className="text-center space-y-6 py-8">
                <div className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-50 to-purple-50 px-4 py-2 rounded-full border border-blue-200">
                    <Zap className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-700">Tecnología de vanguardia</span>
                </div>

                <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent leading-tight">
                    Fotogrametría 3D
                </h1>

                <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                    Transforma tus fotos y videos en modelos 3D detallados usando poderozas herramientas de computer graphics & vision.
                </p>

                <div className="flex items-center justify-center gap-8 pt-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        Procesamiento rápido
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        Alta precisión
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                        <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                        Fácil de usar
                    </div>
                </div>
            </div>

            {/* Options Grid */}
            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                {/* Photos Option */}
                <Card
                    className="group cursor-pointer border-2 border-gray-200 hover:border-green-400 hover:shadow-2xl transition-all duration-300 relative overflow-hidden bg-gradient-to-br from-white via-green-50/30 to-emerald-50/50"
                    onClick={() => onModeSelect('photos')}
                >
                    {/* Background Pattern */}
                    <div className="absolute inset-0 opacity-5 group-hover:opacity-10 transition-opacity">
                        <div className="absolute top-4 right-4 w-32 h-32 border border-green-200 rounded-full"></div>
                        <div className="absolute bottom-4 left-4 w-24 h-24 border border-green-300 rounded-full"></div>
                    </div>

                    <CardHeader className="relative z-10 space-y-4 pb-6">
                        <div className="flex items-center justify-between">
                            <div className="p-3 bg-green-100 rounded-xl group-hover:bg-green-200 transition-colors">
                                <ImageIcon className="w-8 h-8 text-green-600" />
                            </div>
                            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-green-600 group-hover:translate-x-1 transition-all" />
                        </div>

                        <div className="space-y-2">
                            <CardTitle className="text-2xl font-bold text-gray-900 group-hover:text-green-800 transition-colors">
                                Subir Fotos
                            </CardTitle>
                            <CardDescription className="text-base text-gray-600 leading-relaxed">
                                Carga múltiples fotografías en un archivo ZIP para reconstruir objetos con máxima precisión
                            </CardDescription>
                        </div>
                    </CardHeader>

                    <CardContent className="relative z-10 space-y-4">
                        <div className="space-y-3">
                            <Badge variant="secondary" className="bg-green-100 text-green-700 hover:bg-green-200">
                                <Upload className="w-3 h-3 mr-1" />
                                ZIP con imágenes
                            </Badge>

                            <div className="space-y-2">
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                    <Camera className="w-4 h-4 text-green-500" />
                                    <span>Formatos: JPG, PNG, TIFF</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                    <Zap className="w-4 h-4 text-green-500" />
                                    <span>Resolución preservada</span>
                                </div>
                            </div>
                        </div>

                        <div className="pt-2 border-t border-green-100">
                            <p className="text-xs text-gray-500">
                                Ideal para objetos estáticos y máximo detalle
                            </p>
                        </div>
                    </CardContent>
                </Card>

                {/* Video Option */}
                <Card
                    className="group cursor-pointer border-2 border-gray-200 hover:border-blue-400 hover:shadow-2xl transition-all duration-300 relative overflow-hidden bg-gradient-to-br from-white via-blue-50/30 to-sky-50/50"
                    onClick={() => onModeSelect('video')}
                >
                    {/* Background Pattern */}
                    <div className="absolute inset-0 opacity-5 group-hover:opacity-10 transition-opacity">
                        <div className="absolute top-4 right-4 w-32 h-32 border border-blue-200 rounded-full"></div>
                        <div className="absolute bottom-4 left-4 w-24 h-24 border border-blue-300 rounded-full"></div>
                    </div>

                    <CardHeader className="relative z-10 space-y-4 pb-6">
                        <div className="flex items-center justify-between">
                            <div className="p-3 bg-blue-100 rounded-xl group-hover:bg-blue-200 transition-colors">
                                <Video className="w-8 h-8 text-blue-600" />
                            </div>
                            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                        </div>

                        <div className="space-y-2">
                            <CardTitle className="text-2xl font-bold text-gray-900 group-hover:text-blue-800 transition-colors">
                                Subir Video
                            </CardTitle>
                            <CardDescription className="text-base text-gray-600 leading-relaxed">
                                Graba un video girando alrededor del objeto y extrae frames automáticamente
                            </CardDescription>
                        </div>
                    </CardHeader>

                    <CardContent className="relative z-10 space-y-4">
                        <div className="space-y-3">
                            <Badge variant="secondary" className="bg-blue-100 text-blue-700 hover:bg-blue-200">
                                <Film className="w-3 h-3 mr-1" />
                                MP4, AVI, MOV
                            </Badge>

                            <div className="space-y-2">
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                    <Video className="w-4 h-4 text-blue-500" />
                                    <span>Extracción automática de frames</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                    <Zap className="w-4 h-4 text-blue-500" />
                                    <span>Proceso más rápido</span>
                                </div>
                            </div>
                        </div>

                        <div className="pt-2 border-t border-blue-100">
                            <p className="text-xs text-gray-500">
                                Perfecto para captura rápida y objetos complejos
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Features Section */}
            <div className="bg-gray-50 rounded-2xl p-8 border border-gray-200">
                <div className="text-center mb-8">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">¿Cómo funciona?</h3>
                    <p className="text-gray-600">Proceso simple en 3 pasos</p>
                </div>

                <div className="grid md:grid-cols-3 gap-6">
                    <div className="text-center space-y-3">
                        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                            <span className="text-lg font-bold text-blue-600">1</span>
                        </div>
                        <h4 className="font-semibold text-gray-900">Sube tu contenido</h4>
                        <p className="text-sm text-gray-600">Fotos en ZIP o video del objeto</p>
                    </div>

                    <div className="text-center space-y-3">
                        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                            <span className="text-lg font-bold text-green-600">2</span>
                        </div>
                        <h4 className="font-semibold text-gray-900">Procesamiento IA</h4>
                        <p className="text-sm text-gray-600">Algoritmos avanzados analizan las imágenes</p>
                    </div>

                    <div className="text-center space-y-3">
                        <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto">
                            <span className="text-lg font-bold text-purple-600">3</span>
                        </div>
                        <h4 className="font-semibold text-gray-900">Descarga modelo 3D</h4>
                        <p className="text-sm text-gray-600">Modelo 3D listo para usar</p>
                    </div>
                </div>
            </div>
        </div>
    )
}