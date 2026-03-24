import { useEffect, useState } from 'react'

export const useWebSocket = (url: string) => {
  const [lastMessage, setLastMessage] = useState<any>(null)
  const [status, setStatus] = useState<'connecting' | 'open' | 'closed'>('connecting')

  useEffect(() => {
    const ws = new WebSocket(url)

    ws.onopen = () => setStatus('open')
    ws.onclose = () => setStatus('closed')
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setLastMessage(data)
      } catch (e) {
        setLastMessage(event.data)
      }
    }

    return () => ws.close()
  }, [url])

  return { lastMessage, status }
}
