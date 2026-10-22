import { useState, useEffect, useRef, useCallback } from 'react';
import { scanService } from '../services/scanService';

export function useScanPolling(scanId, onStatusChange = null) {
  const [statusData, setStatusData] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);
  const wsRef = useRef(null);

  const fetchStatus = useCallback(async () => {
    if (!scanId) return;
    try {
      const data = await scanService.getScanStatus(scanId);
      setStatusData(data);
      if (onStatusChange) {
        onStatusChange(data);
      }
      return data;
    } catch (err) {
      console.error(`Error polling status for scan ${scanId}:`, err);
      setError(err);
      return null;
    }
  }, [scanId, onStatusChange]);

  useEffect(() => {
    if (!scanId) return;

    let active = true;

    // 1. Initial status fetch
    fetchStatus();

    // 2. Real-time WebSocket connection
    try {
      const isHttps = window.location.protocol === 'https:';
      const wsProtocol = isHttps ? 'wss:' : 'ws:';
      const host = window.location.hostname || 'localhost';
      const wsUrl = `${wsProtocol}//${host}:8000/ws/scans`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.scan_id === Number(scanId)) {
            setStatusData(payload);
            if (onStatusChange) onStatusChange(payload);
            if (payload.status !== 'queued' && payload.status !== 'running') {
              setIsPolling(false);
            }
          }
        } catch {
          // ignore non-json messages
        }
      };

      ws.onerror = () => {
        // Fallback gracefully to polling
      };
    } catch {
      // Environments where WebSocket is not supported
    }

    // 3. Resilient backup polling interval
    const poll = async () => {
      const data = await fetchStatus();
      if (!active) return;

      if (data && (data.status === 'queued' || data.status === 'running')) {
        setIsPolling(true);
        timerRef.current = setTimeout(poll, 4000);
      } else {
        setIsPolling(false);
      }
    };

    poll();

    return () => {
      active = false;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch {
          // ignore
        }
        wsRef.current = null;
      }
    };
  }, [scanId, fetchStatus, onStatusChange]);

  return { statusData, isPolling, error, refetch: fetchStatus };
}
