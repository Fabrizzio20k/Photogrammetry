'use client'

import { ModeSelector } from '../ModeSelector/ModeSelector'
import { FileUpload } from '../FileUpload/FileUpload'
import { PhotoSelector } from '../PhotoSelector/PhotoSelector'
import { ProcessingStatus } from '../ProcessingStatus/ProcessingStatus'
import { CompletedView } from '../CompletedView/CompletedView'
import { PhotogrammetryActions } from '../PhotogrammetryActions/PhotogrammetryActions'
import { usePhotogrammetry } from '@/hooks/usePhotogrammetry'

export default function PhotogrammetryInterface() {
    const {
        mode,
        step,
        uploadedFile,
        message,
        progress,
        photos,
        selectedPhotos,
        showPhotoSelection,
        config,
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
        downloadResult
    } = usePhotogrammetry()

    const togglePhotoSelection = (filename: string) => {
        const newSelected = new Set(selectedPhotos)
        if (newSelected.has(filename)) {
            newSelected.delete(filename)
        } else {
            newSelected.add(filename)
        }
        setSelectedPhotos(newSelected)
    }

    if (step === 'completed') {
        return (
            <CompletedView
                message={message}
                onDownload={downloadResult}
                onReset={reset}
            />
        )
    }

    if (step === 'photogrammetry') {
        return (
            <ProcessingStatus
                progress={progress}
                title="Procesando Fotogrametría"
                description="Esto puede tomar varios minutos..."
            />
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="container mx-auto p-6 max-w-4xl">
                {!mode ? (
                    <ModeSelector onModeSelect={setMode} />
                ) : (
                    <FileUpload
                        mode={mode}
                        step={step}
                        uploadedFile={uploadedFile}
                        config={config}
                        progress={progress}
                        message={message}
                        onModeChange={() => setMode(null)}
                        onFileUpload={(file) => {
                            setUploadedFile(file)
                            setMessage('')
                        }}
                        onConfigChange={setConfig}
                        onFileRemove={() => {
                            setUploadedFile(null)
                            setMessage('')
                        }}
                        onProcess={processFile}
                    />
                )}

                {showPhotoSelection && photos.length > 0 && (
                    <PhotoSelector
                        photos={photos}
                        selectedPhotos={selectedPhotos}
                        onToggleSelection={togglePhotoSelection}
                        onSelectAll={() => setSelectedPhotos(new Set(photos.map(p => p.filename)))}
                        onDeselectAll={() => setSelectedPhotos(new Set())}
                        onConfirm={confirmPhotoSelection}
                        onClose={() => setShowPhotoSelection(false)}
                    />
                )}

                {message && step === 'idle' && !showPhotoSelection && photos.length > 0 && (
                    <PhotogrammetryActions
                        message={message}
                        onViewPhotos={() => setShowPhotoSelection(true)}
                        onStartPhotogrammetry={runPhotogrammetry}
                    />
                )}
            </div>
        </div>
    )
}