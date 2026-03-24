/**
 * useDocuments — Strict TypeScript hook for document management.
 *
 * Strict Mandates:
 *   • NO `: any` — all types explicit
 *   • REST fetching with loading/error states
 *   • Exponential backoff WebSocket reconnection (base 1s, max 30s, jitter)
 *   • Auto-cleanup on unmount
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '../store/authStore';
import { useNotificationStore } from '../store/notificationStore';
import { api } from '../api/axiosClient';
import type { IDocument, IWebSocketEvent } from '../types';

// ---------------------------------------------------------------------------
// Exponential Backoff Config
// ---------------------------------------------------------------------------
const WS_BASE_DELAY_MS = 1_000;
const WS_MAX_DELAY_MS = 30_000;
const WS_JITTER_FACTOR = 0.3;

function getBackoffDelay(attempt: number): number {
  const exponential = Math.min(WS_BASE_DELAY_MS * 2 ** attempt, WS_MAX_DELAY_MS);
  const jitter = exponential * WS_JITTER_FACTOR * Math.random();
  return exponential + jitter;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
interface UseDocumentsReturn {
  documents: IDocument[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  wsStatus: 'connecting' | 'open' | 'closed' | 'reconnecting';
}

export const useDocuments = (): UseDocumentsReturn => {
  const session = useAuthStore((state) => state.session);
  const caFirm = useAuthStore((state) => state.caFirm);
  const addNotification = useNotificationStore((state) => state.addNotification);

  const [documents, setDocuments] = useState<IDocument[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'open' | 'closed' | 'reconnecting'>('closed');

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef<number>(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef<boolean>(true);

  // -----------------------------------------------------------------------
  // REST: Fetch Documents
  // -----------------------------------------------------------------------
  const fetchDocuments = useCallback(async () => {
    if (!session?.access_token) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get<IDocument[]>('/documents/');
      if (isMountedRef.current) {
        setDocuments(response.data);
      }
    } catch (err: unknown) {
      if (isMountedRef.current) {
        const message = err instanceof Error ? err.message : 'Failed to fetch documents';
        setError(message);
        addNotification('Fetch Error', message, 'error');
      }
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [session?.access_token, addNotification]);

  // -----------------------------------------------------------------------
  // WebSocket: Connect with Exponential Backoff Reconnection
  // -----------------------------------------------------------------------
  const connectWebSocket = useCallback(() => {
    if (!caFirm?.id || !isMountedRef.current) return;

    // Clean up any existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const backendWsUrl = import.meta.env.VITE_BACKEND_WS_URL || 'ws://localhost:8000';
    const wsUrl = `${backendWsUrl}/ws/${caFirm.id}`;

    setWsStatus('connecting');

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        setWsStatus('open');
        reconnectAttemptRef.current = 0; // Reset on successful connection
        console.info('[NemoClaw WS] Connected');
      };

      ws.onmessage = (event: MessageEvent) => {
        if (!isMountedRef.current) return;

        try {
          const data = JSON.parse(event.data as string) as IWebSocketEvent;

          switch (data.event) {
            case 'document_received':
              addNotification(
                'New Document Received',
                `via WhatsApp from ${data.client_name ?? 'Unknown'}`,
                'info',
              );
              // Auto-refetch to update the list
              void fetchDocuments();
              break;

            case 'document_processed':
              addNotification(
                'NemoClaw Extraction Complete',
                `Document ${data.document_id ?? ''} processed successfully.`,
                'success',
              );
              void fetchDocuments();
              break;

            case 'anomaly_detected':
              addNotification(
                'Anomaly Detected',
                data.anomaly?.description ?? 'Unknown anomaly',
                'error',
              );
              break;

            default:
              console.warn('[NemoClaw WS] Unknown event:', data);
          }
        } catch {
          console.error('[NemoClaw WS] Failed to parse message:', event.data);
        }
      };

      ws.onclose = (event: CloseEvent) => {
        if (!isMountedRef.current) return;

        console.info(`[NemoClaw WS] Disconnected (code=${event.code})`);
        wsRef.current = null;

        // Don't reconnect on intentional close (1000) or if unmounted
        if (event.code === 1000) {
          setWsStatus('closed');
          return;
        }

        // Exponential backoff reconnection
        setWsStatus('reconnecting');
        const delay = getBackoffDelay(reconnectAttemptRef.current);
        reconnectAttemptRef.current += 1;

        console.info(`[NemoClaw WS] Reconnecting in ${Math.round(delay)}ms (attempt ${reconnectAttemptRef.current})`);
        reconnectTimerRef.current = setTimeout(connectWebSocket, delay);
      };

      ws.onerror = () => {
        // onerror is always followed by onclose, so just log here
        console.error('[NemoClaw WS] Connection error');
      };
    } catch {
      console.error('[NemoClaw WS] Failed to create WebSocket');
      setWsStatus('closed');
    }
  }, [caFirm?.id, addNotification, fetchDocuments]);

  // -----------------------------------------------------------------------
  // Lifecycle
  // -----------------------------------------------------------------------
  useEffect(() => {
    isMountedRef.current = true;

    void fetchDocuments();
    connectWebSocket();

    return () => {
      isMountedRef.current = false;

      // Clean up reconnect timer
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }

      // Clean up WebSocket
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
    };
  }, [fetchDocuments, connectWebSocket]);

  return {
    documents,
    isLoading,
    error,
    refetch: fetchDocuments,
    wsStatus,
  };
};