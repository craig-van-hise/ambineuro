import React, { useState, useCallback } from 'react'
import { Upload, Music, CheckCircle2, AlertCircle } from 'lucide-react'

interface AmbisonicDropZoneProps {
  onFileDrop: (file: File) => void
}

export const AmbisonicDropZone: React.FC<AmbisonicDropZoneProps> = ({ onFileDrop }) => {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      setError(null)

      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile && droppedFile.name.toLowerCase().endsWith('.wav')) {
        setFile(droppedFile)
        onFileDrop(droppedFile)
      } else {
        setError('Please drop a valid .wav Ambisonic file')
      }
    },
    [onFileDrop]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0]
      if (selectedFile && selectedFile.name.toLowerCase().endsWith('.wav')) {
        setFile(selectedFile)
        onFileDrop(selectedFile)
      } else if (selectedFile) {
        setError('Please select a valid .wav Ambisonic file')
      }
    },
    [onFileDrop]
  )

  return (
    <div
      className={`relative group flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-2xl transition-all duration-300 ease-in-out cursor-pointer
        ${
          isDragging
            ? 'border-blue-500 bg-blue-500/10 scale-[1.01]'
            : 'border-gray-700 bg-gray-800/40 hover:border-gray-500 hover:bg-gray-800/60'
        }
        ${error ? 'border-red-500/50' : ''}
      `}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept=".wav"
        onChange={handleFileInput}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />

      <div className="flex flex-col items-center pointer-events-none">
        <div className={`p-4 rounded-full mb-4 transition-transform duration-300 ${isDragging ? 'scale-110' : ''}`}>
          {file ? (
            <Music className="w-12 h-12 text-blue-400" />
          ) : (
            <Upload className={`w-12 h-12 ${isDragging ? 'text-blue-500' : 'text-gray-500'}`} />
          )}
        </div>

        <h3 className="text-xl font-semibold text-gray-200 mb-2">
          {file ? file.name : 'Load Ambisonic File'}
        </h3>
        
        <p className="text-gray-400 text-sm max-w-xs text-center">
          {file 
            ? 'File loaded successfully. Ready for processing.' 
            : 'Drag and drop your .wav spatial audio here or click to browse.'}
        </p>

        {error && (
          <div className="flex items-center mt-4 text-red-400 text-sm animate-pulse">
            <AlertCircle className="w-4 h-4 mr-2" />
            {error}
          </div>
        )}

        {file && !error && (
          <div className="flex items-center mt-4 text-green-400 text-sm">
            <CheckCircle2 className="w-4 h-4 mr-2" />
            WAV format detected
          </div>
        )}
      </div>
    </div>
  )
}
