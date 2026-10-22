# NetSecureLab
## Integrated Network Security Assessment and Reconnaissance Framework

> **Purpose of this document:** Reference specification for implementation of the NetSecureLab course-based project. Use this document as the primary project-context reference when designing, coding, testing, or extending the system.

---

## 1. Project Identity

### Formal Academic Title
**NetSecureLab: An Integrated Network Security Assessment and Reconnaissance Framework**

### Short Project Name
**NetSecureLab**

### Domain
- Computer Networks
- Ethical Hacking / Cybersecurity
- Network Reconnaissance
- Security Assessment

### Core Idea

NetSecureLab is a controlled and authorized security-assessment application that combines several techniques from the Computer Networks and Ethical Hacking laboratory into one workflow.

The system should:

1. Accept an authorized target.
2. Perform selected passive reconnaissance and DNS analysis.
3. Perform Nmap-based host, port, and service discovery.
4. Normalize results from different tools into a common data model.
5. Apply transparent rule-based security checks.
6. Present the results in a web dashboard.
7. Maintain scan history.
8. Compare scans to identify changes.
9. Generate an assessment report.

The application is an **integration and assessment framework**, not a replacement for Nmap or a complete enterprise vulnerability scanner.

---

# 2. Course Alignment

The uploaded CNEH laboratory syllabus covers the following relevant areas:

- Networking commands and connectivity
- FTP / file sharing
- Kali Linux and basic commands
- Passive information gathering
- WHOIS / Netcraft / archive-based reconnaissance
- Search-operator-based information gathering
- Server geolocation
- DNS enumeration
- Mail-server enumeration
- `nslookup`, `host`, and `dig`
- Nmap live-host discovery
- Port scanning
- Service and version detection
- OS detection
- Nmap scripting
- Website vulnerability scanning
- Proxy-based secure hacking

The project should primarily integrate the **reconnaissance, enumeration, scanning, fingerprinting, and security-assessment portion** of the course.

### Explicit syllabus-to-project mapping

| Course area | NetSecureLab feature |
|---|---|
| Networking commands | Network diagnostics / target information |
| Kali Linux | Security-testing environment |
| Passive reconnaissance | Domain / infrastructure intelligence |
| WHOIS / domain information | Reconnaissance module |
| DNS enumeration | DNS Intelligence module |
| Mail-server enumeration | MX / mail infrastructure analysis |
| Nmap live-host discovery | Host discovery |
| Nmap port scanning | Port inventory |
| Service/version detection | Service fingerprinting |
| OS detection | Host fingerprinting |
| Nmap scripts | Selected NSE integration |
| Vulnerability scanning | Rule-based checks + optional web scanner |
| Proxy-based testing | Optional OWASP ZAP integration |

### What should not be artificially added

The following course topics do not need to be forced into the main application:

- Character stuffing
- Bit stuffing
- CRC implementation
- Distance-vector routing simulation
- Generic FTP server implementation
- Basic network setup as a standalone feature

These may be discussed in the course-coverage matrix, but they are not naturally part of a unified security-assessment workflow.

---

# 3. Project Scope

## 3.1 Core Scope (Fully Delivered)

The core framework delivers the complete end-to-end laboratory assessment workflow:

1. **Target Management**: Register, validate, and manage authorized assessment targets (IP, Hostname, Domain, Web Application) with mandatory backend authorization confirmation.
2. **Scan Orchestration**: Execute predefined scan profiles (`Quick`, `Standard`, `Full`) with cooperative cancellation and crash recovery.
3. **Nmap Host Discovery**: Active live host identification via ping sweeps and ARP/ICMP discovery.
4. **Port Inventory & Scanning**: Structured port discovery across standard and full TCP ranges with subprocess timeouts.
5. **Service & Version Fingerprinting**: Protocol extraction, service banners, and software version identification.
6. **Operating System Detection**: Decoupled, non-fatal TCP/IP fingerprinting pass (`-O`) for `full` assessment profiles.
7. **DNS Record Enumeration**: Comprehensive query execution (`A`, `AAAA`, `NS`, `MX`, `TXT`, and `_dmarc.<domain>`) via `dnspython`.
8. **Passive Infrastructure Reconnaissance**: WHOIS domain registrar details, reverse DNS PTR lookups, and graceful failure handling.
9. **Result Normalization**: Translation of tool-specific XML and network responses into a relational schema.
10. **Rule-Based Finding Generation**: 14 transparent, evidence-backed rules (`R001`-`R014`) with module-aware skipping.
11. **Unified Dashboard & UI**: Modern React 18+ SPA with dark-mode theme, statistics counters, and filterable finding views.
12. **Historical Scan Archive**: Persistent storage of scans, snapshots, and raw output files.
13. **Comparative Scan Differencing**: Bidirectional delta analysis detecting new/removed hosts, open ports, service updates, and resolved findings.
14. **Security Assessment Reporting**: Standalone Jinja2 HTML report generator with executive summary, methodology disclaimers, and print-to-PDF styles.

## 3.2 Advanced Extensions & Enterprise Hardening (Fully Delivered)

All three previously planned extensions along with modern enterprise capabilities have been implemented and integrated into the primary pipeline:

15. **Web Application Security Assessment (OWASP ZAP Model)**: Automated HTTP/HTTPS security inspector (`app/services/web_security/scanner.py`) assessing HSTS, CSP, X-Frame-Options, MIME-sniffing, server technology disclosure, cookie flags, and sensitive file exposures (`.env`, `.git/HEAD`) under `source="zap"`.
16. **Nmap NSE Script Parsing & Evaluation**: XML parser extraction of `<script>` blocks, populating `Port.scripts` and triggering cryptographic cipher checks (`R013`) and dangerous HTTP method checks (`R014`).
17. **Interactive Network Topology Visualization**: High-performance SVG network graph (`/topology`) mapping `Targets → Discovered Hosts → Exposed Ports → Findings` with search, pan, zoom, and node inspector.
18. **Real-Time Observability**: WebSocket event broadcasting (`/ws/scans`) for live state transitions and ASGI request correlation middleware (`X-Request-ID` and latency logging).
19. **Automated Scan Scheduling**: Background scheduler worker (`scheduler.py`) supporting recurring automated scans (`daily`, `weekly`, `monthly`).
20. **Finding Lifecycle & Remediation Workflow**: Remediation status tracking (`open`, `acknowledged`, `accepted_risk`, `remediated`) with analyst investigation notes.
21. **Machine-Readable Exports**: Instant CSV (`/findings/export/csv`) and JSON (`/findings/export/json`) exports for SIEM and external workflows.
22. **Authentication & RBAC**: JWT access tokens, bcrypt password hashing, and user roles (`admin`, `operator`).

## 3.3 Explicitly Out of Scope

To preserve ethical laboratory alignment and academic rigor, the following remain strictly out of scope:

- Autonomous exploitation and payload execution
- Credential brute-forcing and password cracking
- Automated attack generation and malware delivery
- Real-time intrusion detection / inline packet blocking
- Autonomous black-box penetration testing
- Speculative ML/LLM-based threat hallucination
- Enterprise multi-vendor configuration compliance
- Unrestricted public Internet scanning without authorization

The project operates strictly upon authorized targets in controlled laboratory and educational environments.

---

# 4. Design Philosophy

The main technical contribution is **integration**.

Do not implement another Nmap clone.

Do not build a custom port scanner unless specifically required for a demonstration.

Do not build a complete vulnerability scanner from scratch.

Instead:

```text
Existing Security Tools
        |
        v
Collection / Adapters
        |
        v
Normalization
        |
        v
Common Data Model
        |
        v
Rule-Based Finding Engine
        |
        +------------------+
        |                  |
        v                  v
   Dashboard            Report
        |
        v
   Scan Comparison
```

The application should hide tool-specific output formats behind adapters.

---

# 5. High-Level Architecture

```text
                                  +------------------------------------------+
                                  |         React 18+ Single Page App        |
                                  | (Dashboard, Targets, Topology, Findings) |
                                  +---------------------+--------------------+
                                                        |
                                +-----------------------+-----------------------+
                                | REST API (Axios)      | WebSockets (/ws/scans)|
                                v                       v                       v
     +---------------------------------------------------------------------------------+
     |                               FastAPI Backend                                   |
     |   RequestCorrelationMiddleware (X-Request-ID, Latency) | JWT Security & RBAC    |
     +------------------------------------------+--------------------------------------+
                                                |
                +-------------------------------+-------------------------------+
                |                               |                               |
                v                               v                               v
         API Controllers             Background Scan Worker          Recurring Scheduler
     (/targets, /scans, /auth,     (ThreadPoolExecutor workers=1)    (Background Thread)
     /findings, /topology, etc.)                |                               |
                                                v                               |
                                        Scan Orchestrator                       |
                                                |                               |
        +------------------+--------------------+------------------+            |
        |                  |                    |                  |            |
        v (Stage 1)        v (Stage 2)          v (Stage 3)        |            |
       Nmap               DNS                  Recon               |            |
   Subprocess         dnspython            python-whois            |            |
  (XML Parser)        (A, MX, TXT)      (Passive Registry)         |            |
        |                  |                    |                  |            |
        +------------------+--------------------+------------------+            |
                           |                                                    |
                           v (Normalized Storage)                               |
            +---------------------------------------+                           |
            |        SQLite Relational Store        |<--------------------------+
            |        (PRAGMA foreign_keys=ON)       |
            +-------------------+-------------------+
                                |
                                v (Stage 4)
                        Finding Rule Engine
                     (14 Rules: R001 - R014)
                                |
                                v (Stage 5)
                    Web Security Assessment (ZAP)
                   (8 Rules: WEB-001 - WEB-007-GIT)
                                |
                +---------------+---------------+
                |                               |
                v                               v
        Scan Comparison &                Report Generator
       Topology Visualizer               (Jinja2 + Print PDF)
```

---

# 6. Technology Stack (Implemented & Verified)

## Frontend
- **Framework**: React 18+ SPA initialized via Vite
- **Routing**: React Router v6
- **Styling**: Vanilla CSS Modules (custom tokens, dark-mode design system, glassmorphism)
- **HTTP Client**: Axios with request/response interceptors for auth tokens and correlation tracking
- **Real-Time Streaming**: Native WebSocket client (`/ws/scans`) with automatic polling fallback
- **Interactive Visualization**: Native SVG graph engine for network topology rendering
- **Testing & Quality**: Vitest component test suite (10 tests, 100% pass) and Oxlint (0 warnings, 0 errors)

## Backend
- **Framework**: Python 3.11+ / FastAPI with Pydantic v2 data models
- **Database ORM**: SQLAlchemy 2.0 (Sync) with SQLite, PRAGMA foreign key constraints, and startup migrations
- **Concurrency & Scheduling**: In-process `ThreadPoolExecutor(max_workers=1)` for scans and background daemon thread for recurring schedules
- **Security & RBAC**: PyJWT for cryptographic bearer tokens, Passlib with Bcrypt for password hashing
- **Observability**: ASGI `RequestCorrelationMiddleware` injecting `X-Request-ID` and timing latency, with `CorrelationIdFilter` Python logging

## Network & Security Tooling
- **Active Scanning**: Nmap subprocess execution with XML parsing (`xml.etree.ElementTree`) and NSE script analysis
- **DNS Intelligence**: `dnspython` for authoritative and recursive querying of standard and DMARC TXT records
- **Passive Reconnaissance**: `python-whois` and standard `socket` libraries for registrar lookup and reverse DNS PTR queries
- **Web Application Assessment**: `httpx` client performing active header, cookie, and path posture checks (source: `zap`)

## Reporting & Production
- **Reporting**: Jinja2 templating engine generating standalone HTML assessment reports with print-to-PDF media queries
- **Containerization**: Multi-stage Docker builds with Nginx reverse proxy and Docker Compose orchestration
- **Test Coverage**: 34 backend pytest integration and unit tests (100% pass)

---

# 7. Module 1: Target Management

## Purpose

Create, validate, and maintain targets that are explicitly authorized for security assessment.

## Target Types

Canonical normalization (`TargetNormalizer`) handles:

- **IP Address**: IPv4 addresses (e.g. `192.168.56.101`, `127.0.0.1`)
- **Hostname**: Local or intranet hostnames (e.g. `web01.corp.local`)
- **Domain**: Fully-qualified domains (e.g. `scanme.nmap.org`, `example.com`)
- **Web Application URL**: HTTP/HTTPS URLs (e.g. `http://192.168.56.102:3000`)

## Target fields

```text
Target
------
id: Integer (Primary Key)
name: String (Descriptive label)
target: String (Raw target string)
target_type: Enum ('ip', 'hostname', 'domain', 'web_application')
description: String (Optional context)
authorization_confirmed: Boolean (Mandatory technical gate)
schedule_interval: String ('daily', 'weekly', 'monthly', or None)
schedule_profile: String ('quick', 'standard', 'full')
next_scheduled_at: DateTime (UTC timestamp for recurring scan execution)
created_at: DateTime (UTC creation timestamp)
```

## Technical Controls & Enforcement

1. **Authorization Confirmation**: Scans cannot be executed against any target where `authorization_confirmed` is false. Attempts to initiate a scan return HTTP 403 Forbidden.
2. **Deletion Protection**: To preserve auditability and prevent historical data corruption, targets with associated scans cannot be deleted (`DELETE /targets/{id}` returns HTTP 409 Conflict).
3. **Automated Scheduling**: Operators can configure recurring scans via `PATCH /targets/{id}/schedule`, managed by the background `scheduler.py` worker.

---

# 8. Module 2: Scan Management

## Scan Profiles

Scan profiles are strictly managed by the backend (`app/config.py`) to eliminate command-injection risks:

### Quick Scan
- **Objective**: Rapid live host discovery
- **Arguments**: `-sn` (ping sweep, no port scanning)
- **Execution Target**: Canonical host/IP

### Standard Scan
- **Objective**: Typical surface enumeration and service detection
- **Arguments**: `-sV -T4` (top 1,000 TCP ports with version banner grabbing)
- **Execution Target**: Canonical host/IP

### Full Assessment
- **Objective**: Comprehensive security assessment
- **Arguments**: `-sV -sC -T4 -p-` (all 65,535 TCP ports, default NSE scripts, version detection)
- **Decoupled Passes**: Secondary non-fatal OS detection pass (`-O`) and targeted script parsing (`ssl-enum-ciphers`, `http-methods`)

## Safety Controls & Execution Guards

- **Hard Timeout Cap**: Enforced execution timeout (`SCAN_TIMEOUT = 600s`, hard cap `MAX_SCAN_TIMEOUT = 1800s`). If a subprocess exceeds this threshold, it is terminated and marked `failed`.
- **Active Scan Concurrency Guard**: Rejects scan creation (HTTP 409 Conflict) if the target already has an active scan (`queued` or `running`).
- **Cooperative Cancellation**: Pipeline stages check `scan.cancel_requested` between execution phases to halt execution gracefully.
- **Stale Scan Recovery**: On application boot, any scans lingering in `running` or `queued` state due to process termination are marked `failed` with explanatory messages.
- **Real-Time WebSockets**: Live status broadcasts emitted via `/ws/scans` notify the frontend UI instantaneously of stage transitions.

## Scan record

```text
Scan
----
id: Integer (Primary Key)
target_id: Integer (Foreign Key -> Target.id, ondelete RESTRICT)
profile: Enum ('quick', 'standard', 'full')
status: Enum ('queued', 'running', 'completed', 'failed', 'cancelled')
cancel_requested: Boolean (Cooperative cancellation flag)
started_at: DateTime (UTC start timestamp)
completed_at: DateTime (UTC finish timestamp)
duration: Float (Execution duration in seconds)
raw_output_path: String (Filesystem path to raw Nmap XML)
nmap_status: Enum ('pending', 'success', 'failed', 'skipped')
dns_status: Enum ('pending', 'success', 'partial', 'failed', 'skipped')
recon_status: Enum ('pending', 'success', 'partial', 'failed', 'skipped')
error_message: String (Descriptive failure reason if applicable)
```

---

# 9. Module 3: Nmap Integration

Nmap is the primary network-assessment engine.

Use **machine-readable XML output** for integration rather than scraping terminal text.

## Data to extract

### Host level
- IP address
- Hostname
- Host status
- Address type
- Basic OS information if available

### Port level
- Port number
- Protocol
- State
- Service
- Product
- Version
- Extra information

### Script level
- Script ID
- Script output
- Host/port association

## Data flow

```text
Target
  |
  v
Nmap
  |
  v
XML output
  |
  v
XML parser
  |
  v
Normalized Python objects
  |
  v
Database
```

## Adapter interface

Conceptually:

```python
class NmapAdapter:
    def run_scan(target, profile):
        ...

    def parse_xml(xml_path):
        ...

    def normalize_results(parsed_results):
        ...
```

The frontend should never need to know how Nmap works internally.

---

# 10. Module 4: DNS Intelligence

This module maps directly to the DNS and mail-server enumeration portion of the course.

## Records to support

Mandatory:

- A
- AAAA
- NS
- MX
- TXT

Optional:

- CNAME
- SOA
- PTR

## Example

```text
Domain: example.local

A
192.168.1.20

NS
ns1.example.local

MX
mail.example.local

TXT
...
```

## DNS data model

```text
DNSRecord
---------
id
target_id
record_type
name
value
ttl
collected_at
```

## UI

A dedicated DNS Intelligence page should contain:

- Domain
- A/AAAA results
- Nameservers
- Mail servers
- TXT records
- Optional additional records

---

# 11. Module 5: Passive Reconnaissance

This module should remain intentionally focused.

## Goals

Collect basic information without performing aggressive probing.

Possible categories:

- Domain information
- Name servers
- Mail servers
- Resolved IP addresses
- Registration/domain metadata where available
- Basic infrastructure information

The project may reference course techniques such as WHOIS, archive-based information, search operators, and server geolocation, but should not attempt to recreate the entire public Internet as an OSINT engine.

## Design principle

External data sources can fail.

Therefore:

```text
Source available
      |
      v
Collect data
      |
      v
Normalize
```

and:

```text
Source unavailable
      |
      v
Record graceful error
      |
      v
Continue assessment
```

The application should not fail completely because one external source is unavailable.

---

# 12. Module 6: Common Result Model

Different tools produce different formats. The backend normalizes them into common relational entities stored in SQLite (`PRAGMA foreign_keys = ON`).

## User

```text
User
----
id: Integer (Primary Key)
username: String (Unique)
email: String
hashed_password: String (Bcrypt hashed)
role: String ('admin', 'operator')
is_active: Boolean
created_at: DateTime (UTC)
```

## Asset

```text
Asset
-----
id: Integer (Primary Key)
scan_id: Integer (Foreign Key -> Scan.id)
ip: String (IPv4 address)
hostname: String (Optional reverse or DNS hostname)
status: String ('up', 'down')
os: String (OS signature string if detected)
discovered_at: DateTime (UTC)
```

## Port

```text
Port
----
id: Integer (Primary Key)
asset_id: Integer (Foreign Key -> Asset.id)
port_number: Integer (e.g. 80, 443, 22)
protocol: String ('tcp', 'udp')
state: String ('open', 'filtered', 'closed')
service: String (Service name, e.g. 'http', 'ssh')
product: String (Software product, e.g. 'Apache httpd', 'OpenSSH')
version: String (Software version, e.g. '2.4.52')
extra_info: String (Additional banner details)
scripts: String (JSON-serialized NSE script outputs: [{'id': ..., 'output': ...}])
```

## DNS Record

```text
DNSRecord
---------
id: Integer (Primary Key)
target_id: Integer (Foreign Key -> Target.id)
scan_id: Integer (Foreign Key -> Scan.id)
record_type: String ('A', 'AAAA', 'MX', 'NS', 'TXT')
name: String (Query record name, e.g. '_dmarc.example.com')
value: String (Record data string)
ttl: Integer (Time to live)
collected_at: DateTime (UTC)
```

## Recon Result

```text
ReconResult
-----------
id: Integer (Primary Key)
target_id: Integer (Foreign Key -> Target.id)
scan_id: Integer (Foreign Key -> Scan.id)
category: String ('whois', 'rdns', 'geo')
key: String (Property name, e.g. 'registrar', 'country')
value: String (Extracted value)
source: String ('whois', 'socket')
collected_at: DateTime (UTC)
```

## Finding

```text
Finding
-------
id: Integer (Primary Key)
scan_id: Integer (Foreign Key -> Scan.id)
asset_id: Integer (Optional Foreign Key -> Asset.id)
rule_id: String (Traceable rule identifier, e.g. 'R001', 'WEB-001')
category: String (Taxonomy category, e.g. 'Service Exposure', 'Web Security')
title: String (Concise summary of observation)
description: String (Detailed technical explanation)
severity: Enum ('critical', 'high', 'medium', 'low', 'informational')
status: Enum ('open', 'acknowledged', 'accepted_risk', 'remediated')
evidence: Text (Observed command/banner output or header proof)
source: String ('nmap', 'dns', 'recon', 'zap')
recommendation: Text (Actionable administrative guidance)
notes: Text (Analyst investigation notes and audit remarks)
created_at: DateTime (UTC)
```

---

# 13. Module 7: Rule-Based Finding Engine

The finding engine is deterministic, evidence-backed, and transparent.

## Why rule-based?

- Transparent and defensible during viva evaluations
- Deterministic, unit-testable, and reproducible
- Zero hallucination risk (unlike generative AI approaches)
- Does not require a training dataset or statistical assumptions
- Directly reinforces Computer Networks protocols and Ethical Hacking risk principles

## Complete Rules Catalog

### Network & Infrastructure Rules (Source: `nmap` and `dns`)

| Rule ID | Title | Trigger Condition | Severity | Category | Source |
|---|---|---|---|---|---|
| `R001` | FTP Service Reachable | TCP/21 open | Medium | Service Exposure | `nmap` |
| `R002` | Telnet Service Reachable | TCP/23 open | Medium | Service Exposure | `nmap` |
| `R003` | Database Service Reachable | TCP 3306, 5432, 1433, 1521, or 27017 open | Medium | Service Exposure | `nmap` |
| `R004` | SMB/NetBIOS Service Reachable | TCP 139 or 445 open | Medium | Service Exposure | `nmap` |
| `R005` | RDP Service Reachable | TCP/3389 open | Low | Service Exposure | `nmap` |
| `R006` | Web Service Detected | TCP 80, 443, 8080, 8443 open with HTTP | Informational | Web Discovery | `nmap` |
| `R007` | SSH Service Detected | TCP/22 open | Informational | Service Info | `nmap` |
| `R008` | Service Version Identified | Software version extracted by banner probe | Informational | Fingerprinting | `nmap` |
| `R009` | OS Fingerprint Identified | OS detection signature returned | Informational | Fingerprinting | `nmap` |
| `R010` | SPF Record Not Found | No TXT record starting with `v=spf1` (domain targets) | Low | DNS Security | `dns` |
| `R011` | DMARC Record Not Found | No TXT record at `_dmarc.<domain>` (domain targets) | Low | DNS Security | `dns` |
| `R012` | Multiple MX Servers | More than one MX record detected | Informational | Mail Infrastructure | `dns` |
| `R013` | Insecure SSL/TLS Weak Ciphers | Obsolete ciphers/protocols in NSE script output | Medium | Cryptographic Security | `nmap` |
| `R014` | Dangerous HTTP Methods Enabled | Risky methods (PUT, DELETE, TRACE) in NSE output | Low | Web Security | `nmap` |

### Web Application Posture Rules (Source: `zap`)

Integrated into Stage 5 of the scan orchestrator (`app/services/web_security/scanner.py`):

| Rule ID | Title | Trigger Condition | Severity | Category |
|---|---|---|---|---|
| `WEB-001` | Missing HSTS Header | HTTPS endpoint missing `Strict-Transport-Security` | Medium | Web Security |
| `WEB-001-HTTP` | Unencrypted HTTP In Use | Web service running over cleartext HTTP | Medium | Web Security |
| `WEB-002` | Missing Content Security Policy | Missing `Content-Security-Policy` header | Medium | Web Security |
| `WEB-003` | Missing Clickjacking Protection | Missing `X-Frame-Options` and CSP `frame-ancestors` | Medium | Web Security |
| `WEB-004` | Missing MIME-Sniffing Protection | Missing `X-Content-Type-Options: nosniff` | Low | Web Security |
| `WEB-005` | Server / Tech Disclosure | Disclosed `Server` or `X-Powered-By` headers | Informational | Information Disclosure |
| `WEB-006` | Insecure Cookie Flags | Session cookie missing `Secure` or `HttpOnly` flags | Low | Web Security |
| `WEB-007` | Exposed `.env` Configuration | Accessible `.env` file containing secrets/keys | High | Sensitive Data Exposure |
| `WEB-007-GIT` | Exposed `.git` Metadata | Accessible `.git/HEAD` repository directory | High | Sensitive Data Exposure |

## Module-Aware Execution

The finding engine respects collection module outcome statuses:
- If `nmap_status == "failed"`, port-based rules (`R001`-`R009`, `R013`, `R014`) are skipped rather than falsely reporting zero findings.
- If `dns_status == "failed"`, DNS rules (`R010`-`R012`) are skipped.
- Every finding includes mandatory evidence, rule ID traceability, and practical administrative remediation guidance.

---

# 14. Findings Data Requirements

Every finding should answer:

1. What was found?
2. Where was it found?
3. Why was it created?
4. Which tool produced the evidence?
5. What evidence supports it?
6. What should the administrator review?

Example:

```text
Finding
------------------------------------------------
Title:
Exposed FTP Service

Asset:
192.168.56.101

Port:
21/TCP

Category:
Service Exposure

Severity:
Defined according to project rules

Evidence:
Nmap identified an FTP service on TCP/21.

Source:
Nmap

Recommendation:
Review whether FTP is required and restrict or
replace the service where appropriate.
```

---

# 15. Severity Model

Use a small classification:

- High
- Medium
- Low
- Informational

The project must document the rule used to assign severity.

Do not present the severity as a universal or complete risk score.

For example, a rule can state:

```text
Severity = High
when the project-specific policy classifies direct
exposure of a sensitive service as high priority.
```

The report should distinguish:

- observed fact
- project rule
- recommendation

---

# 16. Module 8: Dashboard

The dashboard should be information-dense but minimal.

## Primary metrics

```text
Targets
Hosts Discovered
Open Ports
Services Identified
Findings
```

## Example

```text
NETSECURELAB

Targets                4
Hosts Discovered       8
Open Ports             21
Services               14
Findings                7
```

## Findings summary

```text
High           2
Medium         3
Low            1
Informational  1
```

## Recent scans

```text
Target              Status       Findings
192.168.56.101      Completed       3
lab.example.local   Completed       2
```

Avoid unnecessary decorative graphs.

---

# 17. Main UI Pages

The frontend is a single-page application built with React 18+ and CSS Modules, adhering to a high-contrast dark-mode design system.

## Navigation Structure

```text
Dashboard (/): Aggregated statistics, recent scans, finding severity breakdown
Targets (/targets): Authorized target inventory, registration modal, recurring scheduler
Topology (/topology): Interactive SVG graph mapping Targets -> Hosts -> Ports -> Findings
Scans (/scans): Scan execution history, active progress indicators, cancellation controls
Scan Detail (/scans/:id): In-depth host snapshots, ports, services, DNS, recon, raw XML
Scan Comparison (/compare): Bidirectional diff between scans of the same target
Findings (/findings): Enterprise finding table, lifecycle management, notes drawer, CSV/JSON export
Reports (/reports): Standalone HTML report viewer with print-to-PDF export
```

## Detailed View Capabilities

### Targets View (`/targets` & `/targets/:id`)
- Register new authorized targets with explicit confirmation checkbox
- Real-time scan history per target
- Configure recurring automated scans (daily, weekly, monthly) via interactive modal
- Target deletion protection when historical scans exist

### Network Topology View (`/topology`)
- Native SVG rendering of relational graph hierarchies: `Targets → Discovered Hosts → Exposed Services → Findings`
- Search bar to locate specific IPs, hostnames, or service names
- Category filters to toggle node visibility (Targets, Hosts, Services, Findings)
- Interactive zoom, pan, and click-to-inspect side drawer displaying node properties and vulnerabilities

### Findings View (`/findings`)
- Multi-dimensional filters (Severity: Critical, High, Medium, Low, Info; Category; Source: Nmap, DNS, Recon, ZAP)
- Remediation lifecycle selector: `open` &rarr; `acknowledged` &rarr; `accepted_risk` &rarr; `remediated`
- Analyst investigation notes drawer allowing custom remediation remarks
- One-click machine-readable exports: **Export to CSV** and **Export to JSON**

### Reports View (`/reports/:scan_id`)
- Generates and views standalone HTML assessment reports
- Formats evidence, observed ports, DNS records, and methodology disclaimers
- Print-to-PDF trigger with dedicated `@media print` styling

---

# 18. Module 9: Scan Comparison

This high-value capability transforms NetSecureLab into a continuous security assessment framework by comparing normalized snapshots across scans of the same target.

## Comparison Diff Engine

```text
Scan 1 (Baseline Snapshot)
          +
Scan 2 (Current Snapshot)
          |
          v
Difference Engine (app/services/comparison/)
          |
          +---> Discovered / Removed Hosts
          +---> Newly Opened / Closed Ports
          +---> Service & Banner Version Changes
          +---> New Findings / Resolved Findings
```

---

# 19. Module 10: Reporting

Generates formal, standalone security assessment reports using Jinja2 templating.

## Report Principles

- Executive assessment overview and target metadata
- Distinguishes observed technical facts from administrative recommendations
- Full evidence disclosure for every finding with rule ID traceability
- Methodological limitations and non-destructive testing disclaimers
- Responsive HTML view and seamless print-to-PDF formatting via `@media print`

---

# 20. Web Security Module: Integrated Web Application Posture (ZAP Model)

Corresponds to the web security and proxy assessment component of the course syllabus. It runs automatically in Stage 5 of the scan orchestrator (`app/services/web_security/scanner.py`) whenever HTTP/HTTPS services or domain targets are detected.

## Implementation Architecture

```text
Discovered Web Endpoint (HTTP/HTTPS)
                 |
                 v
   Web Security Scanner (httpx client)
   (Passive header & active baseline checks)
                 |
                 v
   Posture Evaluation (HSTS, CSP, Cookies, Headers, .env, .git)
                 |
                 v
   Normalized Findings (source = "zap")
                 |
                 v
   Unified Finding Store & Dashboard
```

## Evaluated Rules (`source="zap"`)

1. `WEB-001`: Missing HTTP Strict Transport Security (HSTS) on HTTPS endpoints.
2. `WEB-001-HTTP`: Unencrypted HTTP Service in use without TLS redirection.
3. `WEB-002`: Missing Content Security Policy (CSP) header.
4. `WEB-003`: Missing Clickjacking Protection (`X-Frame-Options` and CSP `frame-ancestors`).
5. `WEB-004`: Missing MIME-Sniffing Protection (`X-Content-Type-Options: nosniff`).
6. `WEB-005`: Server & Framework Version Disclosure (`Server`, `X-Powered-By`).
7. `WEB-006`: Insecure Session Cookie Flags (Missing `Secure` or `HttpOnly`).
8. `WEB-007` & `WEB-007-GIT`: Exposed Configuration Files (`.env`, `.git/HEAD`).

All web security findings map directly to the common `Finding` schema with `source="zap"`, appearing seamlessly on the Dashboard, Findings page, and generated reports without modifying frontend models.

---

# 21. Backend API Reference

The FastAPI backend exposes a clean REST API and WebSocket connection:

## Authentication & RBAC
```text
POST   /auth/login             Authenticate credentials, return signed JWT bearer token
GET    /auth/me                Retrieve current authenticated user profile
POST   /auth/register          Register new user account (requires admin privilege)
```

## Targets & Scheduling
```text
POST   /targets                Register new target (requires authorization_confirmed: true)
GET    /targets                List all targets with scan counts
GET    /targets/{id}           Retrieve detailed target profile
PATCH  /targets/{id}/schedule  Configure recurring schedule (daily, weekly, monthly, none)
DELETE /targets/{id}           Delete target (returns 409 if scans exist)
```

## Scans & Results
```text
POST   /scans                  Create & queue scan ({target_id, profile})
GET    /scans                  List all scans (filterable by target_id)
GET    /scans/{id}             Get scan status, duration, and module outcomes
GET    /scans/{id}/status      Lightweight status endpoint for polling fallback
POST   /scans/{id}/cancel      Request cooperative cancellation of running scan
GET    /scans/{id}/hosts       List discovered host snapshots
GET    /scans/{id}/ports       List discovered open/filtered ports and banners
GET    /scans/{id}/services    List distinct enumerated services
GET    /scans/{id}/dns         List DNS records collected for scan
GET    /scans/{id}/recon       List passive reconnaissance results
GET    /scans/{id}/raw         Secure download of raw Nmap XML file
GET    /scans/compare/{s1}/{s2}Comparative delta diff between two scans
```

## Findings & Lifecycle
```text
GET    /findings               List all findings across scans (filterable)
GET    /findings/export/csv    Export findings matching filters as CSV
GET    /findings/export/json   Export findings matching filters as JSON
PATCH  /findings/{id}          Update remediation status and analyst notes
GET    /scans/{id}/findings    List findings for a specific scan
```

## Network Topology
```text
GET    /topology               Unified graph (nodes and links) for targets, hosts, ports, findings
```

## Reports & System
```text
POST   /reports/{scan_id}/generate  Generate standalone HTML assessment report
GET    /reports/{scan_id}           View rendered HTML report
GET    /reports/{scan_id}/download  Download HTML report file
GET    /dashboard/stats             Global metrics (targets, scans, assets, severity counts)
GET    /health                      System health and application version
```

## Real-Time WebSockets
```text
WS     /ws/scans               Live streaming of scan state changes and stage transitions
```

---

# 22. Repository Structure

```text
NetSecureLab/
|
+-- frontend/
|   +-- src/
|   |   +-- components/
|   |   |   +-- Layout/         AppShell, Navbar, Sidebar
|   |   |   +-- common/         Badge, Modal, Button, Card
|   |   +-- pages/
|   |   |   +-- DashboardPage.jsx
|   |   |   +-- TargetsPage.jsx
|   |   |   +-- TargetDetailPage.jsx
|   |   |   +-- ScansPage.jsx
|   |   |   +-- ScanDetailPage.jsx
|   |   |   +-- ScanComparePage.jsx
|   |   |   +-- FindingsPage.jsx
|   |   |   +-- ReportsPage.jsx
|   |   |   +-- TopologyPage.jsx
|   |   |   +-- TopologyPage.module.css
|   |   +-- services/           api.js, authService.js, findingService.js, topologyService.js
|   |   +-- hooks/              useScanPolling.js (WebSocket with polling fallback)
|   |   +-- test/               Vitest test suites (Badge.test.jsx, Modal.test.jsx)
|   |   +-- App.jsx
|   |   +-- main.jsx
|   +-- package.json
|   +-- vite.config.js
|
+-- backend/
|   +-- app/
|   |   +-- main.py             FastAPI application, lifespan, middleware, routers
|   |   +-- config.py           Application settings, scan timeouts, scan profiles
|   |   +-- api/                API route controllers (targets, scans, findings, auth, topology, etc.)
|   |   +-- database/           connection.py, init_db.py (auto-migrations & crash recovery)
|   |   +-- models/             SQLAlchemy models (Target, Scan, Asset, Port, DNSRecord, Finding, User)
|   |   +-- schemas/            Pydantic schemas for request/response serialization
|   |   +-- services/
|   |   |   +-- nmap/           executor.py, parser.py (XML & NSE), normalizer.py
|   |   |   +-- dns/            service.py (dnspython A, MX, NS, TXT, DMARC)
|   |   |   +-- recon/          service.py (WHOIS and reverse DNS)
|   |   |   +-- findings/       engine.py, rules.py (R001 - R014 catalog)
|   |   |   +-- web_security/   scanner.py (HTTP posture & ZAP model)
|   |   |   +-- reporting/      service.py (Jinja2 HTML report compilation)
|   |   |   +-- scan_orchestrator.py  5-stage execution coordinator
|   |   +-- workers/
|   |   |   +-- scan_worker.py  ThreadPoolExecutor scan worker
|   |   |   +-- scheduler.py    Recurring cron scan scheduler
|   |   +-- utils/              logger.py, security.py (JWT/Bcrypt), auth_deps.py, event_manager.py
|   +-- tests/                  34 pytest tests across all modules
|   +-- requirements.txt
|   +-- pyproject.toml
|
+-- docker-compose.yml          Production multi-container orchestration
+-- Dockerfile.backend          Containerized FastAPI + Nmap environment
+-- Dockerfile.frontend         Containerized React + Nginx reverse proxy
+-- README.md                   Primary user and architectural manual
+-- NetSecureLab.md             Comprehensive reference specification
```

---

# 23. Backend Service Responsibilities

## `nmap_service.py`
Responsible for:
- building approved scan commands
- executing Nmap
- capturing XML
- error handling
- returning structured results

## `dns_service.py`
Responsible for:
- querying DNS records
- normalizing DNS responses
- handling lookup failures

## `recon_service.py`
Responsible for:
- passive domain/infrastructure information
- external-source handling
- normalization

## `finding_engine.py`
Responsible for:
- applying security rules
- generating findings
- assigning project-defined severity
- including evidence and recommendations

## `comparison.py`
Responsible for:
- comparing scan snapshots
- identifying additions/removals/changes

## `report_service.py`
Responsible for:
- converting normalized data into report sections
- generating HTML
- optional PDF output

## `zap_service.py`
Responsible for:
- optional authorized web scanning
- retrieving ZAP findings
- mapping them to the common finding model

---

# 24. Execution and Error Handling

Security tools can take time or fail.

The UI should not assume every scan succeeds.

Represent states clearly:

```text
Queued
Running
Completed
Failed
```

Show a useful failure message.

Examples:

```text
Nmap not installed
Target unreachable
Permission issue
Invalid target
DNS lookup failed
ZAP unavailable
```

Do not expose raw exception traces in the user-facing interface.

Keep detailed logs in the backend.

---

# 25. Security and Safety Requirements

## Authorization

Only support testing of:

- systems owned by the project team
- local virtual machines
- deliberately vulnerable lab targets
- systems where explicit authorization exists

## Target validation

Reject or flag malformed target input.

## Command construction

Do not directly concatenate arbitrary user input into shell commands.

Use safe subprocess execution and validated arguments.

## Secrets

Do not store credentials or API keys in source code.

## Logging

Log:

- scan start
- scan completion
- scan failure
- tool errors
- target identifier
- scan profile

Avoid storing unnecessary sensitive content.

---

# 26. Testing Environment

Recommended controlled environment:

```text
Development Machine
      |
      +---- NetSecureLab
      |
      +---- Linux/Kali VM
      |
      +---- Deliberately vulnerable web application (optional)
```

Suitable controlled targets include:

- your own Linux VM
- a local lab server
- an intentionally vulnerable local application

Avoid relying on a public Internet host for demonstrations.

---

# 27. Functional Test Cases & Automated Testing Suite

The framework includes a comprehensive automated test suite spanning unit, integration, safety control, and UI component tests:

- **Backend (pytest)**: 34 tests across 13 test files (`100% passing`)
- **Frontend (vitest)**: 10 tests across 2 test suites (`100% passing`)
- **Static Analysis (oxlint)**: 0 warnings, 0 errors across 27 frontend source files

## Automated Testing Matrix

| Test Suite / Test ID | Component / Area | Verification Focus | Result |
|---|---|---|---|
| `test_auth_api.py` | Authentication & RBAC | Password hashing, JWT token issue, `/auth/me` profile, admin registration guards, unauthorized access rejection | 4 / 4 Passed |
| `test_targets.py` | Target Management | Valid target creation, IP/domain/URL validation, shell injection character rejection, deletion protection (409 Conflict), authorization check | 7 / 7 Passed |
| `test_target_normalizer.py` | Target Normalizer | Canonical extraction of IP, domain, hostnames, and URLs for downstream collection | 4 / 4 Passed |
| `test_orchestrator.py` | Scan Orchestrator | Stage coordination, cooperative cancellation between stages, independent module error tolerance | 3 / 3 Passed |
| `test_nmap_parser.py` | Nmap & NSE Parser | Host status, port states, banners, and NSE script extraction (`ssl-enum-ciphers`, `http-methods`) from XML fixtures | 3 / 3 Passed |
| `test_finding_engine.py` | Rule Engine | Deterministic evaluation of `R001`-`R014`, evidence formatting, and module-awareness skipping when Nmap/DNS fail | 3 / 3 Passed |
| `test_findings_api.py` | Findings API | Remediation lifecycle updates (`PATCH /findings/{id}`), note persistence, and CSV/JSON export generation | 1 / 1 Passed |
| `test_web_security.py` | Web Assessment (ZAP) | Passive & baseline HTTP/HTTPS posture checks (`WEB-001` to `WEB-007-GIT`), cookie flag analysis, sensitive file disclosure | 2 / 2 Passed |
| `test_topology_api.py` | Network Topology | Graph node and link generation (`Targets → Hosts → Ports → Findings`) and summary statistics | 2 / 2 Passed |
| `test_scheduler.py` | Scan Scheduler | Automated recurring interval evaluation (daily, weekly, monthly), overdue scan triggering, next runtime calculation | 2 / 2 Passed |
| `test_comparison.py` | Scan Comparison | Snapshot diffing, identifying new/removed ports and hosts, service version updates, and resolved findings | 1 / 1 Passed |
| `test_report.py` | Report Generation | Standalone Jinja2 HTML report compilation with findings, evidence, disclaimers, and print-to-PDF styles | 1 / 1 Passed |
| `test_stale_recovery.py` | Crash Recovery | Automatic detection and marking of orphaned `queued`/`running` scans as `failed` on application startup | 1 / 1 Passed |
| `Badge.test.jsx` | Frontend UI | Badge rendering for all severity and status variants (`critical`, `high`, `medium`, `low`, `info`) | 8 / 8 Passed |
| `Modal.test.jsx` | Frontend UI | Modal mounting, focus trap, and Escape key dismissal | 2 / 2 Passed |

---

# 28. Non-Functional Requirements

## Usability
A student or evaluator should be able to start a scan without knowing the exact Nmap command syntax.

## Transparency
Every security finding should expose the evidence and source.

## Reproducibility
The same target and scan profile should produce consistent application behavior, subject to network/tool changes.

## Modularity
Nmap, DNS, recon and optional ZAP integrations should remain separate services/adapters.

## Maintainability
Frontend and backend should be independent layers.

---

# 29. Example End-to-End Flow

```text
1. User opens Dashboard
          |
2. Adds authorized target
          |
3. Selects "Full Assessment"
          |
4. Backend creates Scan
          |
5. Nmap executes
          |
6. XML is parsed
          |
7. Hosts / Ports / Services stored
          |
8. DNS module runs if target is a domain
          |
9. Passive reconnaissance runs
          |
10. Results normalized
          |
11. Finding engine applies rules
          |
12. Dashboard updates
          |
13. User reviews findings
          |
14. User compares with previous scan
          |
15. User generates report
```

Optional:

```text
16. Web target selected
          |
17. ZAP assessment
          |
18. ZAP findings normalized
          |
19. Findings shown in same dashboard
```

---

# 30. Example Assessment

### Input

```text
Target:
192.168.56.101
```

### Nmap result

```text
21/tcp   open ftp
22/tcp   open ssh
80/tcp   open http
3306/tcp open mysql
```

### Normalized result

```text
Asset
192.168.56.101

Services
FTP
SSH
HTTP
MySQL
```

### Findings

```text
Finding 1
Exposed FTP Service

Finding 2
Exposed Database Service

Finding 3
Web Service Detected
```

### Report

```text
Assessment Summary
------------------
Hosts: 1
Open Ports: 4
Services: 4
Findings: 3
```

The exact finding list depends on the documented rules and the actual controlled target.

---

# 31. ML / AI Position

Machine learning is **not part of the required core project**.

Reason:

A network-security assessment framework can already be complete using deterministic networking/security tooling and transparent rules.

ML can be documented as future work:

```text
Future Enhancement
------------------
Network traffic anomaly detection
Attack classification
Temporal attack forecasting
Behavioral analysis
```

If an ML module is eventually added, it should be a separate subsystem rather than something the rest of the application depends on.

---

# 32. Relationship to Major Hackathon Problem Patterns

The project is conceptually aligned with current cybersecurity hackathon themes such as:

- network security assessment
- network attack analysis
- network traffic threat detection
- security compliance assessment
- domain/email intelligence
- infrastructure discovery

The project should **take inspiration from these problem patterns**, not reproduce a hackathon problem statement verbatim.

The course project remains intentionally smaller and focused on techniques that are explicitly covered in the CNEH syllabus.

---

# 33. Important Differentiation from Generic Student Projects

Avoid presenting the project as:

> "Nmap with a GUI."

Instead describe it as:

> "A modular framework that integrates passive reconnaissance, DNS enumeration and Nmap-based network discovery into a unified assessment workflow with normalized results, evidence-backed findings, scan comparison, and reporting."

The differentiating elements are:

1. Multiple syllabus techniques integrated into one pipeline
2. Tool-independent normalized data model
3. Rule-based finding engine
4. Scan-history comparison
5. Consolidated dashboard
6. Structured reporting

---

# 34. Academic Contribution

The project demonstrates:

### Networking
- host discovery
- DNS
- ports
- services
- infrastructure discovery

### Cybersecurity
- reconnaissance
- enumeration
- fingerprinting
- vulnerability-oriented checks
- web security assessment

### Software Engineering
- REST API
- modular services
- database design
- asynchronous/background processing
- frontend/backend integration
- report generation

This combination explains why the project is appropriate for a Computer Networks and Ethical Hacking laboratory.

---

# 35. Documentation Requirements

The project documentation should contain:

## Chapter 1 — Introduction
- motivation
- problem definition
- objectives
- scope

## Chapter 2 — Background
- network reconnaissance
- DNS enumeration
- Nmap
- vulnerability assessment
- passive reconnaissance

## Chapter 3 — System Design
- architecture
- modules
- data flow
- database schema
- API design

## Chapter 4 — Implementation
- frontend
- backend
- Nmap integration
- DNS integration
- finding engine
- comparison engine
- reporting

## Chapter 5 — Testing
- test cases
- controlled targets
- results
- screenshots

## Chapter 6 — Limitations
- tool dependency
- external-source availability
- rule-based coverage
- controlled-target requirement

## Chapter 7 — Future Scope
- ZAP expansion
- topology visualization
- traffic analysis
- ML-based anomaly detection

## Chapter 8 — Conclusion

---

# 36. Suggested README Structure

```text
# NetSecureLab

## Overview
## Problem Statement
## Objectives
## Features
## Architecture
## Tech Stack
## Installation
## Configuration
## Running the Backend
## Running the Frontend
## Configuring Nmap
## Optional ZAP Setup
## Database
## API
## Testing
## Security / Authorization
## Limitations
## Future Scope
```

---

# 37. Demo Narrative

The project demonstration should tell one coherent story:

```text
Target
  ↓
Discover
  ↓
Enumerate
  ↓
Analyze
  ↓
Identify findings
  ↓
Compare
  ↓
Report
```

Example presentation order:

1. Show dashboard.
2. Add an authorized lab target.
3. Start assessment.
4. Show Nmap host and port results.
5. Show service/version information.
6. Show DNS intelligence.
7. Show generated findings and their evidence.
8. Show scan history.
9. Run/compare a second scan.
10. Show detected changes.
11. Generate the report.
12. Optionally demonstrate ZAP against a local web application.

---

# 38. Scope-Creep Rules

The following rules should guide implementation decisions:

### Rule 1
If a feature requires building an entirely new security subsystem, postpone it.

### Rule 2
If an existing tool already performs the specialized security task, integrate its supported output rather than rebuilding it.

### Rule 3
If a feature cannot be clearly connected to the course syllabus, it should not be a core feature.

### Rule 4
Every finding should have evidence.

### Rule 5
Do not make ML/AI a dependency of the core system.

### Rule 6
Keep the demo reproducible in a controlled environment.

### Rule 7
Prefer a smaller fully working feature over a large partially working feature.

---

# 39. Definition of Done (Verified & Complete)

The NetSecureLab project has satisfied all core requirements, optional extensions, and enterprise architecture standards:

- [x] **Canonical Target Normalization**: Target input validation and normalization across IP, hostname, domain, and web application URLs.
- [x] **Technical Authorization Control**: Backend rejection (HTTP 403) of scans on unconfirmed targets; protected target deletion (HTTP 409).
- [x] **Scan Orchestration & Safety**: Multi-stage execution with hard timeouts (`MAX_SCAN_TIMEOUT = 1800s`), duplicate scan concurrency guards, and cooperative cancellation.
- [x] **Active Nmap Enumeration**: Host discovery, port scanning, service versioning, decoupled OS detection, and XML script parsing (`Port.scripts`).
- [x] **DNS & Recon Intelligence**: Independent collection of A, AAAA, MX, NS, TXT, DMARC records, and WHOIS/rDNS enrichment.
- [x] **Deterministic Finding Engine**: 14 transparent rules (`R001`-`R014`) with evidence formatting and module-awareness skipping.
- [x] **Integrated Web Application Security (ZAP Module)**: Stage 5 automated HTTP/HTTPS checks (`WEB-001`-`WEB-007-GIT`) mapped to `source="zap"`.
- [x] **Interactive Network Topology**: High-performance SVG visualization (`/topology`) rendering nodes, links, search filters, and side drawer.
- [x] **Real-Time Observability**: Live WebSocket streaming (`/ws/scans`) with polling fallback and request correlation middleware (`X-Request-ID` and latency).
- [x] **Automated Scan Scheduling**: Background scheduler worker (`scheduler.py`) supporting recurring automated scans (`daily`, `weekly`, `monthly`).
- [x] **Finding Lifecycle & Exports**: Remediation tracking (`open`, `acknowledged`, `accepted_risk`, `remediated`), analyst notes, and CSV/JSON exports.
- [x] **Authentication & RBAC**: JWT bearer tokens, bcrypt password hashing, and user roles (`admin`, `operator`).
- [x] **Scan-to-Scan Comparison**: Bidirectional diffing of normalized snapshots across scans of the same target.
- [x] **Reporting Engine**: Standalone HTML assessment reports with methodology disclaimers, limitations, and print-to-PDF formatting.
- [x] **Automated Testing & Quality**: 34 backend pytest tests (100% pass), 10 frontend vitest tests (100% pass), and 0 oxlint warnings/errors.
- [x] **Production Containerization**: Multi-stage Dockerfiles with Nginx reverse proxy and Docker Compose configuration.
