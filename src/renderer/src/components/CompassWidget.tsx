import React from 'react'
import { Compass, Smartphone, Sliders } from 'lucide-react'

interface CompassWidgetProps {
  orientation: {
    yaw: number
    pitch: number
    roll: number
  }
  oscActive: boolean
  onManualChange: (orientation: { yaw?: number, pitch?: number, roll?: number }) => void
}

export const CompassWidget: React.FC<CompassWidgetProps> = ({ 
  orientation, 
  oscActive,
  onManualChange
}) => {
  const { yaw, pitch, roll } = orientation

  return (
    <div className="w-full p-6 bg-gray-900/60 border border-gray-800 rounded-2xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-500/10 rounded-lg">
            <Compass className="w-5 h-5 text-purple-400" />
          </div>
          <h2 className="text-lg font-semibold text-gray-100">Head Tracking</h2>
        </div>
        <div className={`flex items-center space-x-2 px-2 py-1 rounded-full border ${oscActive ? 'bg-green-500/10 border-green-500/20' : 'bg-gray-800 border-gray-700'}`}>
          <Smartphone className={`w-3 h-3 ${oscActive ? 'text-green-400' : 'text-gray-500'}`} />
          <span className={`text-[10px] font-bold uppercase tracking-tighter ${oscActive ? 'text-green-400' : 'text-gray-500'}`}>
            {oscActive ? 'OSC Active' : 'OSC Offline'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        {/* Visual Indicator */}
        <div className="relative flex items-center justify-center py-4">
          <div className="w-32 h-32 rounded-full border-2 border-gray-800 flex items-center justify-center relative">
            {/* Inner ring */}
            <div className="w-24 h-24 rounded-full border border-gray-700/50 flex items-center justify-center">
              {/* Head representation */}
              <div 
                className="w-12 h-16 bg-gradient-to-b from-blue-500 to-purple-600 rounded-t-full rounded-b-2xl transition-transform duration-100 shadow-xl shadow-blue-900/20"
                style={{ 
                  transform: `rotate(${yaw}deg) rotateX(${-pitch}deg) rotateZ(${roll}deg)` 
                }}
              >
                <div className="absolute top-2 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-white/40 rounded-full"></div>
              </div>
            </div>
            
            {/* Axis labels */}
            <span className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-6 text-[8px] font-bold text-gray-600 uppercase">Front</span>
            <span className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-6 text-[8px] font-bold text-gray-600 uppercase">Back</span>
          </div>
        </div>

        {/* Controls/Values */}
        <div className="space-y-4">
          {[
            { label: 'Yaw', value: yaw, key: 'yaw', min: -180, max: 180 },
            { label: 'Pitch', value: pitch, key: 'pitch', min: -90, max: 90 },
            { label: 'Roll', value: roll, key: 'roll', min: -180, max: 180 },
          ].map((axis) => (
            <div key={axis.label} className="space-y-1.5">
              <div className="flex justify-between items-center px-1">
                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">{axis.label}</span>
                <span className="text-[10px] font-mono text-blue-400 bg-blue-500/5 px-1.5 py-0.5 rounded border border-blue-500/10">
                  {axis.value.toFixed(1)}°
                </span>
              </div>
              <input
                type="range"
                min={axis.min}
                max={axis.max}
                step="0.1"
                value={axis.value}
                onChange={(e) => onManualChange({ [axis.key]: parseFloat(e.target.value) })}
                className="w-full h-1 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500/50 hover:accent-blue-500 transition-all"
              />
            </div>
          ))}
          <div className="pt-2 flex items-center space-x-2 text-gray-600">
            <Sliders className="w-3 h-3" />
            <span className="text-[9px] font-medium uppercase italic">Manual Override Enabled</span>
          </div>
        </div>
      </div>
    </div>
  )
}
