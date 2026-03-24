// @ts-nocheck
import { useEffect, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import { useNotificationStore } from '../store/notificationStore';

export const useDocuments = () => {
  const { caFirm } = useAuthStore();
  const addNotification = useNotificationStore((state: any) => state.addNotification);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!caFirm?.id) return;

    const backendUrl = import.meta.env.VITE_BACKEND_WS_URL || 'ws://localhost:8000';
    ws.current = new WebSocket(`${backendUrl}/ws/${caFirm.id}`);

    ws.current.onopen = () => console.log('NemoClaw WebSocket Connected');
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.event) {
        case 'document_received':
          addNotification('New Document Received', `via WhatsApp from ${data.client_name}`, 'info');
          break;
        case 'document_processed':
          addNotification('NemoClaw Extraction Complete', `Document ${data.document_id} processed successfully.`, 'success');
          break;
        case 'anomaly_detected':
          addNotification('Anomaly Detected', data.anomaly.description, 'error');
          break;
        default:
          console.log('Unknown WS event:', data);
      }
    };

    ws.current.onclose = () => console.log('NemoClaw WebSocket Disconnected');

    return () => {
      ws.current?.close();
    };
  }, [caFirm]);

  return { ws: ws.current };
};