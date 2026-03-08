import React, { useState } from 'react'
import { Cpu, ChevronDown, Check } from 'lucide-react'

type DecoderType = 'A2B' | 'SAF-MagLS' | 'SAF-TA' | 'SAF-LS' | 'SAF-SPR'

interface DecoderEnginePanelProps {
  onDecoderChange: (decoder: DecoderType) => void
}

export const DecoderEnginePanel: React.FC<DecoderEnginePanelProps> = ({ onDecoderChange }) => {
  const [activeDecoder, setActiveDecoder] = useState<DecoderType>('A2B')
  const [isOpen, setIsOpen] = useState(false)

  const decoders: DecoderType[] = ['A2B', 'SAF-MagLS', 'SAF-TA', 'SAF-LS', 'SAF-SPR']

  const handleSelect = (decoder: DecoderType) => {
    setActiveDecoder(decoder)
    onDecoderChange(decoder)
    setIsOpen(false)
  }

  return (
    <div className="w-full p-6 bg-gray-900/60 border border-gray-800 rounded-2xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <Cpu className="w-5 h-5 text-blue-400" />
          </div>
          <h2 className="text-lg font-semibold text-gray-100">Decoder Engine</h2>
        </div>
        <div className="flex items-center space-x-2">
          <span className="flex w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-tighter">Active</span>
        </div>
      </div>

      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`w-full flex items-center justify-between px-4 py-3 bg-gray-800/80 border transition-all duration-200 rounded-xl
            ${isOpen ? 'border-blue-500 ring-4 ring-blue-500/10' : 'border-gray-700 hover:border-gray-600'}
          `}
        >
          <div className="flex flex-col items-start">
            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-0.5">Algorithm</span>
            <span className="text-sm font-medium text-gray-200">{activeDecoder}</span>
          </div>
          <ChevronDown className={`w-5 h-5 text-gray-500 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)}></div>
            <div className="absolute top-full left-0 w-full mt-2 py-2 bg-gray-800 border border-gray-700 rounded-xl shadow-2xl z-20">
              {decoders.map((decoder) => (
                <button
                  key={decoder}
                  onClick={() => handleSelect(decoder)}
                  className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-700/50 transition-colors"
                >
                  <span className={`text-sm ${activeDecoder === decoder ? 'text-blue-400 font-semibold' : 'text-gray-300'}`}>
                    {decoder}
                  </span>
                  {activeDecoder === decoder && <Check className="w-4 h-4 text-blue-400" />}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="p-3 bg-gray-800/40 rounded-lg border border-gray-800/50">
          <span className="block text-[10px] font-bold text-gray-500 uppercase mb-1">Status</span>
          <span className="text-xs text-blue-300 font-medium italic">Processing...</span>
        </div>
        <div className="p-3 bg-gray-800/40 rounded-lg border border-gray-800/50">
          <span className="block text-[10px] font-bold text-gray-500 uppercase mb-1">Latency</span>
          <span className="text-xs text-gray-300 font-medium font-mono">12.4ms</span>
        </div>
      </div>
    </div>
  )
}
