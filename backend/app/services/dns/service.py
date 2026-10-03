from typing import List, Dict, Any, Tuple
import dns.resolver
from sqlalchemy.orm import Session
from app.models.dns_record import DNSRecord
from app.utils.target_normalizer import NormalizedTarget
from app.utils.logger import logger

def query_record_type(resolver: dns.resolver.Resolver, name: str, rtype: str) -> List[Dict[str, Any]]:
    """Helper to query a specific DNS record type safely."""
    results = []
    try:
        answers = resolver.resolve(name, rtype)
        for rdata in answers:
            val = rdata.to_text().strip('"')
            results.append({
                "record_type": rtype,
                "name": name,
                "value": val,
                "ttl": answers.rrset.ttl if answers.rrset else None,
            })
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        pass  # Expected when record doesn't exist
    except dns.exception.Timeout:
        logger.warning(f"DNS timeout querying {rtype} for {name}")
    except Exception as e:
        logger.debug(f"DNS query error for {rtype} on {name}: {e}")
    return results

def collect_and_store_dns(
    target_id: int,
    scan_id: int,
    normalized: NormalizedTarget,
    db: Session,
) -> str:
    """
    Collects DNS records and persists them to the database.
    Returns status: 'success', 'partial', 'failed', or 'skipped'.
    """
    if normalized.is_ip or not normalized.dns_name:
        logger.info(f"Skipping DNS collection for IP-based target ({normalized.original})")
        return "skipped"

    domain = normalized.dns_name
    resolver = dns.resolver.Resolver()
    resolver.timeout = 4.0
    resolver.lifetime = 6.0

    collected_records = []
    query_errors = 0
    total_queries = 0

    # Basic host resolution (for both domain and hostname)
    basic_types = ["A", "AAAA", "CNAME"]
    for rtype in basic_types:
        total_queries += 1
        try:
            records = query_record_type(resolver, domain, rtype)
            collected_records.extend(records)
        except Exception:
            query_errors += 1

    # Domain-level specific queries (only for target_type in 'domain', 'web_application')
    if normalized.target_type in ("domain", "web_application"):
        domain_types = ["NS", "MX", "TXT", "SOA"]
        for rtype in domain_types:
            total_queries += 1
            try:
                records = query_record_type(resolver, domain, rtype)
                collected_records.extend(records)
            except Exception:
                query_errors += 1

        # Explicit DMARC lookup at _dmarc.<domain>
        dmarc_name = normalized.get_dmarc_query()
        if dmarc_name:
            total_queries += 1
            try:
                dmarc_records = query_record_type(resolver, dmarc_name, "TXT")
                collected_records.extend(dmarc_records)
            except Exception:
                query_errors += 1

    # Persist records with uniqueness constraint handling
    inserted_count = 0
    for rec in collected_records:
        existing = (
            db.query(DNSRecord)
            .filter(
                DNSRecord.scan_id == scan_id,
                DNSRecord.record_type == rec["record_type"],
                DNSRecord.name == rec["name"],
                DNSRecord.value == rec["value"],
            )
            .first()
        )
        if not existing:
            new_record = DNSRecord(
                target_id=target_id,
                scan_id=scan_id,
                record_type=rec["record_type"],
                name=rec["name"],
                value=rec["value"],
                ttl=rec["ttl"],
            )
            db.add(new_record)
            inserted_count += 1

    db.commit()
    logger.info(f"DNS collection for scan {scan_id} finished: {inserted_count} records saved")

    if not collected_records and query_errors > 0:
        return "failed"
    elif query_errors > 0:
        return "partial"
    return "success"
