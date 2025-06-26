import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CheckCircle, Eye, Play } from 'lucide-react'

interface PhotogrammetryActionsProps {
    message: string
    onViewPhotos: () => void
    onStartPhotogrammetry: () => void
}

export function PhotogrammetryActions({ message, onViewPhotos, onStartPhotogrammetry }: PhotogrammetryActionsProps) {
    return (
        <Card>
            <CardContent className="pt-6">
                <div className="text-center space-y-4">
                    <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                        <CheckCircle className="w-6 h-6 text-green-600" />
                    </div>
                    <p className="text-gray-900 font-medium">{message}</p>
                    <div className="flex gap-3 justify-center">
                        <Button variant="outline" onClick={onViewPhotos}>
                            <Eye className="w-4 h-4 mr-2" />
                            Ver/Editar Fotos
                        </Button>
                        <Button onClick={onStartPhotogrammetry} size="lg">
                            <Play className="w-4 h-4 mr-2" />
                            Iniciar Fotogrametría
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}