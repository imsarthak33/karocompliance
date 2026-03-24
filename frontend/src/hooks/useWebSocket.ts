/**
 * useWebSocket — Generic resilient WebSocket hook with exponential backoff.
 *
 * Strict Mandates:
 *   • NO `: any` — strict IWebSocketEvent typing
 *   • Exponential backoff reconnection
 *   • Auto-cleanup on unmount
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import type { IWebSocketEvent } from '../types';

const WS_BASE_DELAY_MS = 1_000;
const WS_MAX_DELAY_MS = 30_000;
const WS_JITTER_FACTOR = 0.3;

function getBackoffDelay(attempt: number): number {
  const exponential = Math.min(WS_BASE_DELAY_MS * 2 ** attempt, WS_MAX_DELAY_MS);
  const jitter = exponential * WS_JITTER_FACTOR * Math.random();
  return exponential + jitter;
}

type WSStatus = 'connecting' | 'open' | 'closed' | 'reconnecting';

interface UseWebSocketReturn {
  lastMessage: IWebSocketEvent | null;
  status: WSStatus;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [lastMessage, setLastMessage] = useState<IWebSocketEvent | null>(null);
  const [status, setStatus] = useState<WSStatus>('connecting');

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef<number>(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef<boolean>(true);

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('connecting');

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        setStatus('open');
        reconnectAttemptRef.current = 0;
      };

      ws.onclose = (event: CloseEvent) => {
        if (!isMountedRef.current) return;
        wsRef.current = null;

        if (event.code === 1000) {
          setStatus('closed');
          return;
        }

        setStatus('reconnecting');
        const delay = getBackoffDelay(reconnectAttemptRef.current);
        reconnectAttemptRef.current += 1;
        reconnectTimerRef.current = setTimeout(connect, delay);
      };

      ws.onmessage = (event: MessageEvent) => {
        if (!isMountedRef.current) return;
        try {
          const data = JSON.parse(event.data as string) as IWebSocketEvent;
          setLastMessage(data);
        } catch {
          console.error('[WS] Failed to parse message:', event.data);
        }
      };

      ws.onerror = () => {
        console.error('[WS] Connection error');
      };
    } catch {
      setStatus('closed');
    }
  }, [url]);

  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      isMountedRef.current = false;

      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }

      if (wsRef.current) {
        wsRef.current.close(1000, 'Hook unmounted');
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { lastMessage, status };
};
