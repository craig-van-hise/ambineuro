import React from 'react'
import { Play, Pause, Square, SkipBack, SkipForward, Volume2 } from 'lucide-react'

interface TransportBarProps {
  playing: boolean
  position: number
  duration: number
  volume: number
  onPlay: () => void
  onPause: () => void
  onStop: () => void
  onSeek: (pos: number) => void
  onVolumeChange: (vol: number) => void
}

export const TransportBar: React.FC<TransportBarProps> = ({
  playing, position, duration, volume,
  onPlay, onPause, onStop, onSeek, onVolumeChange
}) => {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="fixed bottom-10 left-1/2 -translate-x-1/2 w-[90%] max-w-4xl bg-gray-900/80 border border-gray-800 rounded-2xl p-4 backdrop-blur-lg shadow-2xl z-50">
      <div className="flex flex-col space-y-3">
        {/* Scrubber */}
        <div className="flex items-center space-x-4">
          <span className="text-[10px] font-mono text-gray-500 w-10">{formatTime(position)}</span>
          <input
            type="range"
            min="0"
            max={duration || 100}
            step="0.1"
            value={position}
            onChange={(e) => onSeek(parseFloat(e.target.value))}
            className="flex-1 h-1 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
          <span className="text-[10px] font-mono text-gray-500 w-10">{formatTime(duration)}</span>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <button className="text-gray-500 hover:text-gray-300 transition-colors">
              <SkipBack className="w-5 h-5" />
            </button>
            
            <button 
              onClick={playing ? onPause : onPlay}
              className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center hover:bg-blue-500 transition-all shadow-lg shadow-blue-900/20"
            >
              {playing ? <Pause className="w-5 h-5 text-white" /> : <Play className="w-5 h-5 text-white translate-x-0.5" />}
            </button>

            <button 
              onClick={onStop}
              className="text-gray-500 hover:text-red-400 transition-colors"
            >
              <Square className="w-5 h-5" />
            </button>

            <button className="text-gray-500 hover:text-gray-300 transition-colors">
              <SkipForward className="w-5 h-5" />
            </button>
          </div>

          <div className="flex items-center space-x-3 w-48">
            <Volume2 className="w-4 h-4 text-gray-500" />
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={volume}
              onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
              className="flex-1 h-1 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-gray-400"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
