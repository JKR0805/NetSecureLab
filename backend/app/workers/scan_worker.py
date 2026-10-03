from concurrent.futures import ThreadPoolExecutor
from app.utils.logger import logger

class ScanWorker:
    def __init__(self, max_workers: int = 1):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ScanWorker")
        self._is_shutdown = False

    def submit(self, scan_id: int):
        if self._is_shutdown:
            logger.error(f"Cannot submit scan {scan_id}: ScanWorker is shut down")
            return
        logger.info(f"Submitting scan {scan_id} to background worker")
        try:
            from app.services.scan_orchestrator import run_scan
            self.executor.submit(run_scan, scan_id)
        except Exception as e:
            logger.error(f"Failed to submit scan {scan_id} to orchestrator: {e}")

    def shutdown(self, wait: bool = False):
        logger.info("Shutting down ScanWorker...")
        self._is_shutdown = True
        self.executor.shutdown(wait=wait, cancel_futures=True)
        logger.info("ScanWorker shut down completed.")

scan_worker = ScanWorker()
