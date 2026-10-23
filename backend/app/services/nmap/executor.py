import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.config import settings
from app.utils.logger import logger

class NmapExecutionResult:
    def __init__(
        self,
        success: bool,
        xml_path: Optional[Path] = None,
        stdout: str = "",
        stderr: str = "",
        error_message: Optional[str] = None,
        timed_out: bool = False,
    ):
        self.success = success
        self.xml_path = xml_path
        self.stdout = stdout
        self.stderr = stderr
        self.error_message = error_message
        self.timed_out = timed_out

def execute_nmap_scan(
    scan_target: str,
    profile: str,
    output_xml_path: Path,
    timeout: Optional[int] = None,
    target_port: Optional[int] = None,
) -> NmapExecutionResult:
    """
    Executes Nmap via subprocess with shell=False and strict argument list construction.
    Output path is managed by the backend.
    """
    timeout = timeout or settings.SCAN_TIMEOUT
    profile_args = list(settings.SCAN_PROFILES.get(profile, ["-sV", "-T4", "--top-ports", "1000"]))

    # If target specifies a custom port and profile is standard, ensure that port is probed
    if target_port and profile == "standard":
        profile_args = ["-sV", "-T4", "-p", str(target_port)]

    # Ensure output directory exists
    output_xml_path.parent.mkdir(parents=True, exist_ok=True)

    # Command list construction — never a shell string
    command = [
        settings.NMAP_PATH,
        *profile_args,
        "-oX",
        str(output_xml_path),
        scan_target,
    ]

    logger.info(f"Executing Nmap: {' '.join(command)}")

    try:
        proc = subprocess.run(
            command,
            shell=False,
            timeout=timeout,
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            err = proc.stderr.strip() or f"Nmap exited with return code {proc.returncode}"
            logger.warning(f"Nmap returned non-zero code: {err}")
            # If XML was still generated despite non-zero code, we can check if it exists
            if output_xml_path.exists() and output_xml_path.stat().st_size > 0:
                return NmapExecutionResult(
                    success=True,
                    xml_path=output_xml_path,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                )
            return NmapExecutionResult(
                success=False,
                error_message=err,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )

        if not output_xml_path.exists() or output_xml_path.stat().st_size == 0:
            return NmapExecutionResult(
                success=False,
                error_message="Nmap completed but generated no XML output file",
                stdout=proc.stdout,
                stderr=proc.stderr,
            )

        return NmapExecutionResult(
            success=True,
            xml_path=output_xml_path,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    except subprocess.TimeoutExpired as e:
        logger.error(f"Nmap scan timed out after {timeout}s: {e}")
        return NmapExecutionResult(
            success=False,
            error_message=f"Scan timed out after {timeout} seconds",
            timed_out=True,
        )

    except FileNotFoundError:
        logger.error(f"Nmap binary not found at '{settings.NMAP_PATH}'.")
        return NmapExecutionResult(
            success=False,
            error_message=f"Nmap executable not found at '{settings.NMAP_PATH}'. Please verify Nmap is installed and configured in PATH.",
        )

    except Exception as e:
        logger.error(f"Unexpected error executing Nmap: {e}")
        return NmapExecutionResult(
            success=False,
            error_message=f"Nmap execution error: {str(e)}",
        )

def execute_os_detection(
    scan_target: str,
    output_xml_path: Path,
    timeout: Optional[int] = None,
) -> NmapExecutionResult:
    """
    Executes a separate OS detection pass (-O) for full profile.
    Failure in this pass is non-fatal to the overall scan.
    """
    timeout = timeout or settings.SCAN_TIMEOUT
    output_xml_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        settings.NMAP_PATH,
        "-O",
        "--osscan-limit",
        "-oX",
        str(output_xml_path),
        scan_target,
    ]

    logger.info(f"Executing OS Detection pass: {' '.join(command)}")

    try:
        proc = subprocess.run(
            command,
            shell=False,
            timeout=timeout,
            capture_output=True,
            text=True,
        )

        if output_xml_path.exists() and output_xml_path.stat().st_size > 0:
            return NmapExecutionResult(
                success=True,
                xml_path=output_xml_path,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        return NmapExecutionResult(
            success=False,
            error_message=proc.stderr.strip() or "OS detection produced no output",
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    except Exception as e:
        logger.warning(f"OS detection pass failed (non-fatal): {e}")
        return NmapExecutionResult(
            success=False,
            error_message=str(e),
        )
