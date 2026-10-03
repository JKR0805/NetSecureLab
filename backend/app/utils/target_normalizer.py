import ipaddress
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

@dataclass
class NormalizedTarget:
    original: str
    target_type: str
    scan_target: str       # Clean IP or hostname passed to Nmap
    hostname: Optional[str] = None
    dns_name: Optional[str] = None # Domain/hostname for DNS resolution
    is_ip: bool = False
    scheme: Optional[str] = None
    port: Optional[int] = None

    def get_dmarc_query(self) -> Optional[str]:
        """Returns _dmarc.<domain> if dns_name is available, else None."""
        if self.dns_name and not self.is_ip:
            return f"_dmarc.{self.dns_name}"
        return None

class TargetNormalizer:
    @staticmethod
    def normalize(target_str: str, target_type: str) -> NormalizedTarget:
        """
        Converts any target input (IP, hostname, domain, URL) into a canonical representation
        used by all downstream modules.
        """
        raw = target_str.strip()
        
        # Check if raw target is an IP
        is_ip = False
        try:
            ipaddress.ip_address(raw)
            is_ip = True
        except ValueError:
            is_ip = False

        if target_type == "ip":
            return NormalizedTarget(
                original=raw,
                target_type="ip",
                scan_target=raw,
                hostname=None,
                dns_name=None,
                is_ip=True,
                scheme=None,
                port=None,
            )

        elif target_type in ("domain", "hostname"):
            return NormalizedTarget(
                original=raw,
                target_type=target_type,
                scan_target=raw,
                hostname=raw,
                dns_name=raw if not is_ip else None,
                is_ip=is_ip,
                scheme=None,
                port=None,
            )

        elif target_type == "web_application":
            if not raw.startswith(("http://", "https://")):
                test_url = f"http://{raw}"
            else:
                test_url = raw

            parsed = urlparse(test_url)
            host = parsed.hostname or raw
            parsed_scheme = parsed.scheme if raw.startswith(("http://", "https://")) else None
            parsed_port = parsed.port

            # Check if extracted host is an IP
            try:
                ipaddress.ip_address(host)
                host_is_ip = True
            except ValueError:
                host_is_ip = False

            return NormalizedTarget(
                original=raw,
                target_type="web_application",
                scan_target=host,
                hostname=host,
                dns_name=host if not host_is_ip else None,
                is_ip=host_is_ip,
                scheme=parsed_scheme,
                port=parsed_port,
            )

        # Fallback
        return NormalizedTarget(
            original=raw,
            target_type=target_type,
            scan_target=raw,
            hostname=raw,
            dns_name=raw if not is_ip else None,
            is_ip=is_ip,
        )
