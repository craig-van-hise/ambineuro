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
  const [status, setStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected')
  const [lastError, setLastError] = useState<string | null>(null)
  const [state, setState] = useState<EngineState>({
    playing: false,
    position: 0,
    duration: 0,
    volume: 1.0,
    orientation: { yaw: 0, pitch: 0, roll: 0 },
    osc_active: false
  })
  
  const socketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<any>(null)

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN || 
        socketRef.current?.readyState === WebSocket.CONNECTING) return

    setStatus('connecting')
    // Try 127.0.0.1 first as it's often more reliable than localhost resolution
    const ws = new WebSocket('ws://127.0.0.1:8002')

    ws.onopen = () => {
      console.log('WebSocket connected to Engine')
      setStatus('connected')
      setLastError(null)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'state') {
          const { type, ...engineState } = data
          setState(engineState)
        }
      } catch (e) {
        console.error('Failed to parse message:', e)
      }
    }

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)
      setStatus('disconnected')
      // Reconnect after 2 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 2000)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setLastError('Connection failed. Is the backend running?')
    }

    socketRef.current = ws
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      socketRef.current?.close()
    }
  }, [connect])

  const send = useCallback((message: any) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message))
    }
  }, [])

  return { status, state, send, lastError }
}
