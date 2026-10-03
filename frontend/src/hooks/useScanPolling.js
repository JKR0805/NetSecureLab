import { useState, useEffect, useRef, useCallback } from 'react';
import { scanService } from '../services/scanService';

export function useScanPolling(scanId, onStatusChange = null) {
  const [statusData, setStatusData] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

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

    const poll = async () => {
      const data = await fetchStatus();
      if (!active) return;

      if (data && (data.status === 'queued' || data.status === 'running')) {
        setIsPolling(true);
        timerRef.current = setTimeout(poll, 3000);
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
    };
  }, [scanId, fetchStatus]);

  return { statusData, isPolling, error, refetch: fetchStatus };
}
