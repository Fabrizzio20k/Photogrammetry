import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Loader2 } from 'lucide-react'

interface ProcessingStatusProps {
    progress: number
    title: string
    description: string
}

export function ProcessingStatus({ progress, title, description }: ProcessingStatusProps) {
    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    <Loader2 className="w-16 h-16 text-blue-600 animate-spin mx-auto mb-4" />
                    <CardTitle className="text-2xl">{title}</CardTitle>
                    <CardDescription>{description}</CardDescription>
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