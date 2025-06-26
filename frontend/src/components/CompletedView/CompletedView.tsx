import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CheckCircle, Download } from 'lucide-react'

interface CompletedViewProps {
    message: string
    onDownload: () => void
    onReset: () => void
}

export function CompletedView({ message, onDownload, onReset }: CompletedViewProps) {
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
                    <Button onClick={onDownload} className="w-full" size="lg">
                        <Download className="w-4 h-4 mr-2" />
                        Descargar Resultado
                    </Button>
                    <Button onClick={onReset} variant="outline" className="w-full">
                        Nuevo Proyecto
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}