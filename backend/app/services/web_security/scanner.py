from typing import List, Dict, Any, Optional
from pathlib import Path
import httpx
from sqlalchemy.orm import Session
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.finding import Finding
from app.utils.logger import logger

COMMON_WEB_PORTS = {80, 443, 8000, 8080, 8085, 8443, 8888, 3000, 5000}


def inspect_http_endpoint(
    base_url: str,
    timeout: float = 4.0,
) -> List[Dict[str, Any]]:
    """
    Performs passive and baseline active HTTP/HTTPS security posture checks
    against a discovered web service endpoint.
    """
    findings: List[Dict[str, Any]] = []

    try:
        with httpx.Client(
            verify=False,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "NetSecureLab-WebScanner/1.0"},
        ) as client:
            resp = client.get(base_url)
            headers = {k.lower(): v for k, v in resp.headers.items()}
            is_https = base_url.startswith("https://")

            # 1. HSTS Check
            if is_https:
                if "strict-transport-security" not in headers:
                    findings.append({
                        "rule_id": "WEB-001",
                        "category": "Web Security",
                        "title": "Missing HTTP Strict Transport Security (HSTS) Header",
                        "description": (
                            f"The HTTPS endpoint {base_url} does not declare a Strict-Transport-Security header, "
                            "leaving clients vulnerable to SSL-stripping and man-in-the-middle downgrade attacks."
                        ),
                        "severity": "medium",
                        "evidence": f"Headers returned by {base_url}:\n" + "\n".join(f"{k}: {v}" for k, v in headers.items()),
                        "source": "zap",
                        "recommendation": "Configure 'Strict-Transport-Security: max-age=31536000; includeSubDomains; preload' in web server config.",
                    })
            else:
                findings.append({
                    "rule_id": "WEB-001-HTTP",
                    "category": "Web Security",
                    "title": "Unencrypted HTTP Service In Use",
                    "description": f"The web service at {base_url} communicates over unencrypted cleartext HTTP.",
                    "severity": "medium",
                    "evidence": f"Endpoint URL: {base_url} returned HTTP status {resp.status_code}",
                    "source": "zap",
                    "recommendation": "Migrate web services to TLS/HTTPS and enforce permanent 301 redirection from HTTP to HTTPS.",
                })

            # 2. Content-Security-Policy Check
            if "content-security-policy" not in headers:
                findings.append({
                    "rule_id": "WEB-002",
                    "category": "Web Security",
                    "title": "Missing Content Security Policy (CSP)",
                    "description": (
                        f"The web application at {base_url} does not define a Content-Security-Policy (CSP) header. "
                        "Without CSP, browsers cannot restrict unauthorized scripts, styles, or iframes, increasing risk of XSS."
                    ),
                    "severity": "medium",
                    "evidence": f"Endpoint: {base_url}\nHeaders received: {list(headers.keys())}",
                    "source": "zap",
                    "recommendation": "Define a robust Content-Security-Policy (e.g., default-src 'self'; script-src 'self').",
                })

            # 3. Clickjacking Protection (X-Frame-Options or CSP frame-ancestors)
            has_xfo = "x-frame-options" in headers
            csp = headers.get("content-security-policy", "")
            has_frame_ancestors = "frame-ancestors" in csp

            if not has_xfo and not has_frame_ancestors:
                findings.append({
                    "rule_id": "WEB-003",
                    "category": "Web Security",
                    "title": "Missing Clickjacking Protection (X-Frame-Options)",
                    "description": (
                        f"The web service at {base_url} does not declare 'X-Frame-Options' or CSP 'frame-ancestors'. "
                        "Attackers may frame the site inside transparent iframes to hijack user clicks."
                    ),
                    "severity": "medium",
                    "evidence": f"Endpoint: {base_url}\nMissing X-Frame-Options and frame-ancestors in CSP.",
                    "source": "zap",
                    "recommendation": "Send 'X-Frame-Options: DENY' or 'X-Frame-Options: SAMEORIGIN' on all HTML responses.",
                })

            # 4. MIME-Sniffing Protection (X-Content-Type-Options)
            if headers.get("x-content-type-options", "").lower() != "nosniff":
                findings.append({
                    "rule_id": "WEB-004",
                    "category": "Web Security",
                    "title": "Missing X-Content-Type-Options Header",
                    "description": (
                        f"The endpoint {base_url} is missing 'X-Content-Type-Options: nosniff'. "
                        "Browsers may perform MIME-type sniffing and execute untrusted files as scripts."
                    ),
                    "severity": "low",
                    "evidence": f"Endpoint: {base_url}\nx-content-type-options header: {headers.get('x-content-type-options', 'not set')}",
                    "source": "zap",
                    "recommendation": "Add 'X-Content-Type-Options: nosniff' to HTTP response headers.",
                })

            # 5. Server Banner / Technology Information Disclosure
            disclosed_tech = []
            if "server" in headers:
                disclosed_tech.append(f"Server: {headers['server']}")
            if "x-powered-by" in headers:
                disclosed_tech.append(f"X-Powered-By: {headers['x-powered-by']}")
            if "x-aspnet-version" in headers:
                disclosed_tech.append(f"X-AspNet-Version: {headers['x-aspnet-version']}")

            if disclosed_tech:
                findings.append({
                    "rule_id": "WEB-005",
                    "category": "Information Disclosure",
                    "title": "Web Server / Framework Version Disclosure",
                    "description": (
                        f"The web service at {base_url} exposes underlying server technologies: "
                        f"{', '.join(disclosed_tech)}."
                    ),
                    "severity": "informational",
                    "evidence": f"Endpoint: {base_url}\n" + "\n".join(disclosed_tech),
                    "source": "zap",
                    "recommendation": "Configure the web server to suppress Server tokens and remove 'X-Powered-By' headers.",
                })

            # 6. Cookie Security Flags Check
            cookies = resp.cookies
            for cookie in cookies.jar:
                issues = []
                if not cookie.secure and is_https:
                    issues.append("Missing 'Secure' flag")
                if "httponly" not in [k.lower() for k in cookie._rest.keys()] and not getattr(cookie, "httponly", False):
                    issues.append("Missing 'HttpOnly' flag")

                if issues:
                    findings.append({
                        "rule_id": "WEB-006",
                        "category": "Web Security",
                        "title": f"Insecure Cookie Flags on '{cookie.name}'",
                        "description": (
                            f"Cookie '{cookie.name}' on {base_url} has security weaknesses: {', '.join(issues)}."
                        ),
                        "severity": "low",
                        "evidence": f"Cookie Name: {cookie.name}\nDomain: {cookie.domain}\nWeaknesses: {', '.join(issues)}",
                        "source": "zap",
                        "recommendation": "Ensure all application session cookies are configured with 'Secure', 'HttpOnly', and 'SameSite=Lax/Strict'.",
                    })

            # 7. Sensitive path checks (.env / .git)
            try:
                for sensitive_path in ["/.env", "/.git/HEAD"]:
                    test_url = base_url.rstrip("/") + sensitive_path
                    sens_resp = client.get(test_url, timeout=2.5)
                    if sens_resp.status_code == 200 and len(sens_resp.text) > 0:
                        content_sample = sens_resp.text[:200]
                        if sensitive_path == "/.env" and ("=" in content_sample or "KEY" in content_sample or "DB" in content_sample):
                            findings.append({
                                "rule_id": "WEB-007",
                                "category": "Sensitive Data Exposure",
                                "title": "Exposed Environment Configuration File (.env)",
                                "description": f"An exposed .env configuration file was detected and accessible at {test_url}.",
                                "severity": "high",
                                "evidence": f"URL: {test_url}\nStatus: {sens_resp.status_code}\nContent preview:\n{content_sample}",
                                "source": "zap",
                                "recommendation": "Immediately restrict access to .env files and rotate any compromised secrets/credentials.",
                            })
                        elif sensitive_path == "/.git/HEAD" and "ref: refs/" in content_sample:
                            findings.append({
                                "rule_id": "WEB-007-GIT",
                                "category": "Sensitive Data Exposure",
                                "title": "Exposed Git Repository Metadata (.git/HEAD)",
                                "description": f"Git repository directory structure is publicly accessible at {test_url}.",
                                "severity": "high",
                                "evidence": f"URL: {test_url}\nStatus: {sens_resp.status_code}\nContent preview:\n{content_sample}",
                                "source": "zap",
                                "recommendation": "Configure web server rules to deny all access to hidden dotfiles and .git directories.",
                            })
            except Exception:
                pass

    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as e:
        logger.debug(f"Web assessment connection failed for {base_url}: {e}")
    except Exception as e:
        logger.debug(f"Web assessment error inspecting {base_url}: {e}")

    return findings


def run_web_assessment(scan_id: int, db: Session) -> List[Finding]:
    """
    Orchestrates web security assessment for all discovered web assets and ports.
    Stores findings into the database with source="zap".
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        return []

    assets = db.query(Asset).filter(Asset.scan_id == scan_id).all()
    created_findings: List[Finding] = []

    # Map of (asset_id, endpoint_url) to test
    endpoints_to_test: List[Dict[str, Any]] = []

    is_docker = Path("/.dockerenv").exists()

    for asset in assets:
        for port in asset.ports:
            if port.state != "open":
                continue
            svc = (port.service or "").lower()
            if port.port_number in COMMON_WEB_PORTS or "http" in svc or "ssl" in svc:
                is_https = port.port_number in (443, 8443) or "https" in svc or "ssl" in svc
                scheme = "https" if is_https else "http"
                host_str = asset.hostname if asset.hostname else asset.ip
                if is_docker and host_str in ("127.0.0.1", "localhost"):
                    host_str = "host.docker.internal"
                url = f"{scheme}://{host_str}:{port.port_number}"
                endpoints_to_test.append({
                    "asset_id": asset.id,
                    "url": url,
                })

    # Always test declared target URL if target is a web_application
    if scan.target and getattr(scan.target, "target_type", "") == "web_application":
        target_val = getattr(scan.target, "target", "")
        if target_val:
            raw_url = target_val if target_val.startswith(("http://", "https://")) else f"http://{target_val}"
            if is_docker:
                for loopback in ("127.0.0.1", "localhost"):
                    if loopback in raw_url:
                        raw_url = raw_url.replace(loopback, "host.docker.internal")
            endpoints_to_test.append({"asset_id": None, "url": raw_url})
            # If target declared with https but server only listens on http, test http as well
            if raw_url.startswith("https://"):
                endpoints_to_test.append({"asset_id": None, "url": raw_url.replace("https://", "http://", 1)})

    # If no open ports were identified, test domain/hostname fallback
    elif not endpoints_to_test and scan.target and getattr(scan.target, "target_type", "") in ("domain", "hostname"):
        target_val = getattr(scan.target, "target", "")
        if target_val:
            endpoints_to_test.append({"asset_id": None, "url": f"https://{target_val}"})
            endpoints_to_test.append({"asset_id": None, "url": f"http://{target_val}"})

    # Deduplicate URLs
    seen_urls = set()
    for item in endpoints_to_test:
        u = item["url"]
        if u in seen_urls:
            continue
        seen_urls.add(u)

        logger.info(f"[Scan {scan_id}] Running Web Security Assessment against {u}...")
        findings_data = inspect_http_endpoint(u)
        for fd in findings_data:
            f = Finding(
                scan_id=scan_id,
                asset_id=item["asset_id"],
                rule_id=fd["rule_id"],
                category=fd["category"],
                title=fd["title"],
                description=fd["description"],
                severity=fd["severity"],
                evidence=fd["evidence"],
                source=fd["source"],
                recommendation=fd["recommendation"],
            )
            db.add(f)
            created_findings.append(f)

    if created_findings:
        db.commit()
        logger.info(f"[Scan {scan_id}] Web Security Assessment generated {len(created_findings)} findings.")

    return created_findings
