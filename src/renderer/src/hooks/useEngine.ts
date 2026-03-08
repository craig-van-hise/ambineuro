import { useEffect, useState, useRef, useCallback } from 'react'

export interface EngineState {
  playing: boolean
  position: number
  duration: number
  volume: number
  orientation: {
    yaw: number
    pitch: number
    roll: number
  }
  osc_active: boolean
}

export const useEngine = () => {
  const [status, setStatus] = useState<'connected' | 'disconnected'>('disconnected')
  const [state, setState] = useState<EngineState>({
    playing: false,
    position: 0,
    duration: 0,
    volume: 1.0,
    orientation: { yaw: 0, pitch: 0, roll: 0 },
    osc_active: false
  })
  
  const socketRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket('ws://localhost:8001')

    ws.onopen = () => {
      console.log('WebSocket connected to ws://localhost:8001')
      setStatus('connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'state') {
          const { type, ...engineState } = data
          setState(engineState)
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', event.data, e)
      }
    }

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)
      setStatus('disconnected')
      setTimeout(connect, 2000)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    socketRef.current = ws
  }, [])

  useEffect(() => {
    connect()
    return () => {
      socketRef.current?.close()
    }
  }, [connect])

  const send = useCallback((message: any) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message))
    }
  }, [])

  return { status, state, send }
}
