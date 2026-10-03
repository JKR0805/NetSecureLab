import ipaddress
import re
from urllib.parse import urlparse
from typing import Tuple

SHELL_INJECTION_CHARS = set(";&|`$><\n\r\'\"()!{}[]*?^~")

HOSTNAME_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
)

DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)

def contains_shell_injection(value: str) -> bool:
    """Check if string contains any shell metacharacters."""
    return any(c in SHELL_INJECTION_CHARS for c in value)

def validate_target_input(target: str, target_type: str) -> Tuple[bool, str]:
    """
    Validate target string against its declared target_type.
    Returns (is_valid, error_message).
    """
    if not target or not target.strip():
        return False, "Target cannot be empty"

    target = target.strip()

    if contains_shell_injection(target):
        return False, "Target contains illegal or unsafe characters"

    if target_type == "ip":
        try:
            ipaddress.ip_address(target)
            return True, ""
        except ValueError:
            return False, f"'{target}' is not a valid IPv4 or IPv6 address"

    elif target_type == "domain":
        if not DOMAIN_REGEX.match(target) or len(target) > 253:
            return False, f"'{target}' is not a valid domain name (e.g. scanme.nmap.org or example.com)"
        return True, ""

    elif target_type == "hostname":
        if not HOSTNAME_REGEX.match(target) or len(target) > 253:
            return False, f"'{target}' is not a valid hostname"
        return True, ""

    elif target_type == "web_application":
        parsed = urlparse(target)
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            # Check if domain-like without scheme
            if DOMAIN_REGEX.match(target) or HOSTNAME_REGEX.match(target):
                return True, ""
            return False, "Web application URL must begin with http:// or https:// or be a valid domain/host"
        if not parsed.hostname:
            return False, "Web application URL must include a valid hostname or IP address"
        if contains_shell_injection(parsed.hostname):
            return False, "Host in URL contains illegal characters"
        return True, ""

    return False, f"Unknown target type: '{target_type}'. Must be one of: ip, hostname, domain, web_application"
