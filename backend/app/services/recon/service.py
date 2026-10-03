import socket
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.recon_result import ReconResult
from app.utils.target_normalizer import NormalizedTarget
from app.utils.logger import logger

def collect_and_store_recon(
    target_id: int,
    scan_id: int,
    normalized: NormalizedTarget,
    db: Session,
) -> str:
    """
    Collects passive reconnaissance data (Reverse DNS, WHOIS enrichment).
    WHOIS is treated as optional enrichment — failure does not fail the scan.
    Returns status: 'success', 'partial', 'failed', or 'skipped'.
    """
    results: List[Dict[str, str]] = []
    whois_attempted = False
    whois_succeeded = False

    # 1. Reverse DNS / Host Resolution
    try:
        if normalized.is_ip:
            try:
                host_info = socket.gethostbyaddr(normalized.scan_target)
                if host_info and host_info[0]:
                    results.append({
                        "category": "network",
                        "key": "reverse_dns",
                        "value": str(host_info[0]),
                        "source": "dns",
                    })
            except (socket.herror, socket.gaierror):
                pass
        else:
            try:
                resolved_ip = socket.gethostbyname(normalized.scan_target)
                if resolved_ip:
                    results.append({
                        "category": "network",
                        "key": "resolved_ip",
                        "value": str(resolved_ip),
                        "source": "dns",
                    })
            except socket.gaierror:
                pass
    except Exception as e:
        logger.debug(f"Reverse DNS resolution failed: {e}")

    # 2. WHOIS Enrichment (Domain targets or domain-based web applications)
    domain_to_query = normalized.dns_name
    if domain_to_query and not normalized.is_ip and normalized.target_type in ("domain", "web_application"):
        whois_attempted = True
        try:
            import whois
            logger.info(f"Querying WHOIS for {domain_to_query}")
            w = whois.whois(domain_to_query)
            if w:
                whois_succeeded = True
                if w.registrar:
                    results.append({
                        "category": "registrar",
                        "key": "registrar",
                        "value": str(w.registrar),
                        "source": "whois",
                    })
                if w.creation_date:
                    val = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
                    results.append({
                        "category": "registrar",
                        "key": "creation_date",
                        "value": str(val),
                        "source": "whois",
                    })
                if w.expiration_date:
                    val = w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date
                    results.append({
                        "category": "registrar",
                        "key": "expiration_date",
                        "value": str(val),
                        "source": "whois",
                    })
                if w.name_servers:
                    ns_list = w.name_servers if isinstance(w.name_servers, list) else [w.name_servers]
                    for ns in ns_list:
                        results.append({
                            "category": "nameserver",
                            "key": "nameserver",
                            "value": str(ns).lower(),
                            "source": "whois",
                        })
                if w.status:
                    stat_list = w.status if isinstance(w.status, list) else [w.status]
                    for s in stat_list[:3]:  # Limit to 3 statuses
                        results.append({
                            "category": "domain_info",
                            "key": "status",
                            "value": str(s),
                            "source": "whois",
                        })
        except Exception as e:
            logger.warning(f"Optional WHOIS enrichment unavailable for {domain_to_query}: {e}")

    # Persist results with uniqueness constraint handling
    inserted = 0
    for r in results:
        existing = (
            db.query(ReconResult)
            .filter(
                ReconResult.scan_id == scan_id,
                ReconResult.category == r["category"],
                ReconResult.key == r["key"],
                ReconResult.value == r["value"],
                ReconResult.source == r["source"],
            )
            .first()
        )
        if not existing:
            rec = ReconResult(
                target_id=target_id,
                scan_id=scan_id,
                category=r["category"],
                key=r["key"],
                value=r["value"],
                source=r["source"],
            )
            db.add(rec)
            inserted += 1

    db.commit()
    logger.info(f"Recon collection for scan {scan_id} saved {inserted} entries")

    if whois_attempted and not whois_succeeded and not results:
        return "partial"
    elif whois_attempted and not whois_succeeded:
        return "partial"
    return "success" if results else "skipped"
