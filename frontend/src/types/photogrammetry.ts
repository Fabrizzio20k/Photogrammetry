export type Mode = 'photos' | 'video' | null
export type ProcessStep = 'idle' | 'uploading' | 'processing' | 'selecting' | 'photogrammetry' | 'completed'

export interface Photo {
    filename: string
    size: number
    url: string
}

export interface Config {
    numFrames: number
    segmentObjects: boolean
    reductionPercentage: number
}