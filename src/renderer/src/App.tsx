import { AmbisonicDropZone } from './components/AmbisonicDropZone'
import { SOFADropZone } from './components/SOFADropZone'
import { DecoderEnginePanel } from './components/DecoderEnginePanel'
import { CompassWidget } from './components/CompassWidget'
import { TransportBar } from './components/TransportBar'
import { useEngine } from './hooks/useEngine'
import { Activity, Radio, Waves } from 'lucide-react'

function App() {
  const { status, state, send } = useEngine()

  const handleAmbisonicDrop = (file: File) => {
    console.log('Ambisonic file dropped:', file.name)
    send({ type: 'load_audio', path: (file as any).path })
  }

  const handleSOFADrop = (file: File) => {
    console.log('SOFA file dropped:', file.name)
    send({ type: 'load_hrtf', path: (file as any).path })
  }

  const handleDecoderChange = (decoder: string) => {
    console.log('Decoder changed to:', decoder)
    send({ type: 'set_decoder', decoder })
  }

  const handleManualOrientation = (newOri: { yaw?: number, pitch?: number, roll?: number }) => {
    send({ 
      type: 'set_orientation', 
      orientation: { ...state.orientation, ...newOri } 
    })
  }

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-200 p-8 pb-32 font-sans selection:bg-blue-500/30">
      {/* Header */}
      <header className="max-w-7xl mx-auto flex items-center justify-between mb-12">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/20">
            <Waves className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">AmbiNeuro</h1>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-widest">Neural Spatial Renderer</p>
          </div>
        </div>

        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2 px-3 py-1.5 bg-slate-900/50 border border-slate-800 rounded-full">
            <div className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500'}`}></div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Engine: {status}
            </span>
          </div>
          <Activity className="w-5 h-5 text-slate-600 hover:text-blue-400 cursor-pointer transition-colors" />
        </div>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-12 gap-8">
        {/* Left Column: Audio Loading */}
        <div className="col-span-12 lg:col-span-7 space-y-8">
          <section className="space-y-4">
            <div className="flex items-center space-x-2 text-slate-400 mb-2">
              <Radio className="w-4 h-4 text-blue-500" />
              <h2 className="text-sm font-bold uppercase tracking-widest">Input Stream</h2>
            </div>
            <AmbisonicDropZone onFileDrop={handleAmbisonicDrop} />
          </section>

          <section className="space-y-4">
            <div className="flex items-center space-x-2 text-slate-400 mb-2">
              <Activity className="w-4 h-4 text-purple-500" />
              <h2 className="text-sm font-bold uppercase tracking-widest">HRTF Configuration</h2>
            </div>
            <SOFADropZone onFileDrop={handleSOFADrop} />
          </section>
        </div>

        {/* Right Column: Controls & Visuals */}
        <div className="col-span-12 lg:col-span-5 space-y-8">
          <section className="relative z-30">
            <DecoderEnginePanel onDecoderChange={handleDecoderChange} />
          </section>
          
          <section className="relative z-10">
            <CompassWidget 
              orientation={state.orientation} 
              oscActive={state.osc_active}
              onManualChange={handleManualOrientation}
            />
          </section>
        </div>
      </main>

      {/* Transport */}
      <TransportBar 
        playing={state.playing}
        position={state.position}
        duration={state.duration}
        volume={state.volume}
        onPlay={() => send({ type: 'play' })}
        onPause={() => send({ type: 'pause' })}
        onStop={() => send({ type: 'stop' })}
        onSeek={(pos) => send({ type: 'seek', position: pos })}
        onVolumeChange={(vol) => send({ type: 'set_volume', volume: vol })}
      />

      {/* Footer / Status Bar */}
      <footer className="fixed bottom-0 left-0 right-0 h-10 bg-[#0a0a0c]/80 backdrop-blur-md border-t border-slate-900 px-8 flex items-center justify-between z-40">
        <div className="flex items-center space-x-6">
          <span className="text-[10px] text-slate-600 font-mono">CPU: 12.4%</span>
          <span className="text-[10px] text-slate-600 font-mono">MEM: 156MB</span>
        </div>
        <div className="text-[10px] text-slate-600 font-medium tracking-tighter uppercase">
          v1.0.0-beta • Experimental Neural Branch
        </div>
      </footer>
    </div>
  )
}

export default App
