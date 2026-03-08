import React, { useState, useCallback } from 'react'
import { FileCode, Settings2, AlertCircle } from 'lucide-react'

interface SOFADropZoneProps {
  onFileDrop: (file: File) => void
}

export const SOFADropZone: React.FC<SOFADropZoneProps> = ({ onFileDrop }) => {
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
      if (droppedFile && droppedFile.name.toLowerCase().endsWith('.sofa')) {
        setFile(droppedFile)
        onFileDrop(droppedFile)
      } else {
        setError('Please drop a valid .sofa HRTF file')
      }
    },
    [onFileDrop]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0]
      if (selectedFile && selectedFile.name.toLowerCase().endsWith('.sofa')) {
        setFile(selectedFile)
        onFileDrop(selectedFile)
      } else if (selectedFile) {
        setError('Please select a valid .sofa HRTF file')
      }
    },
    [onFileDrop]
  )

  return (
    <div
      className={`relative group flex flex-row items-center justify-between w-full h-20 px-6 border border-dashed rounded-xl transition-all duration-300 ease-in-out cursor-pointer
        ${
          isDragging
            ? 'border-purple-500 bg-purple-500/10'
            : 'border-gray-700 bg-gray-900/40 hover:border-gray-600 hover:bg-gray-800/40'
        }
        ${error ? 'border-red-500/50' : ''}
      `}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept=".sofa"
        onChange={handleFileInput}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />

      <div className="flex items-center space-x-4 pointer-events-none">
        <div className={`p-2 rounded-lg ${isDragging ? 'bg-purple-500/20' : 'bg-gray-800'}`}>
          <FileCode className={`w-6 h-6 ${isDragging ? 'text-purple-400' : 'text-gray-400'}`} />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-200">
            {file ? file.name : 'Custom HRTF (.sofa)'}
          </span>
          <span className="text-xs text-gray-500">
            {file ? 'HRTF Profile loaded' : 'Drag or click to load profile'}
          </span>
        </div>
      </div>

      <div className="flex items-center pointer-events-none">
        {error ? (
          <AlertCircle className="w-5 h-5 text-red-500 animate-pulse" />
        ) : file ? (
          <div className="px-2 py-1 rounded-md bg-green-500/10 text-green-400 text-[10px] font-bold uppercase tracking-wider">
            Ready
          </div>
        ) : (
          <Settings2 className="w-5 h-5 text-gray-600 group-hover:text-gray-400 transition-colors" />
        )}
      </div>
    </div>
  )
}
