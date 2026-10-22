# NetSecureLab (v3.0)
### Integrated Network Security Assessment & Reconnaissance Framework

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![React Version](https://img.shields.io/badge/react-18%2B-cyan.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests: Pytest](https://img.shields.io/badge/tests-34%20passed-brightgreen.svg)](https://docs.pytest.org/)
[![Tests: Vitest](https://img.shields.io/badge/vitest-10%20passed-green.svg)](https://vitest.dev/)
[![Linter: Oxlint](https://img.shields.io/badge/oxlint-0%20warnings-brightgreen.svg)](https://oxc-project.github.io/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

NetSecureLab is an enterprise-grade, integrated network security assessment and reconnaissance framework developed for authorized laboratory and educational environments. It combines active network discovery, service enumeration, DNS intelligence, passive reconnaissance, automated web application security posture checks, and rule-based security policy evaluation into a single automated pipeline with live WebSocket updates, interactive network topology graphing, historical scan diffing, finding remediation workflows, and standalone assessment reporting.

---

## Table of Contents

1. [Overview & Problem Statement](#overview--problem-statement)
2. [Key Capabilities & Modern Extensions](#key-capabilities--modern-extensions)
3. [Architecture Overview](#architecture-overview)
4. [Technology Stack](#technology-stack)
5. [Installation & Setup](#installation--setup)
6. [Running the Application](#running-the-application)
7. [Default Credentials](#default-credentials)
8. [API Reference](#api-reference)
9. [Security Rules Catalog](#security-rules-catalog)
10. [Automated Testing & Code Quality](#automated-testing--code-quality)
11. [Technical Controls & Ethical Scope](#technical-controls--ethical-scope)
12. [Limitations & Methodology Scope](#limitations--methodology-scope)
13. [License & Course Attribution](#license--course-attribution)

---

## 1. Overview & Problem Statement

Network administrators and security engineers often rely on disparate, disconnected command-line tools (Nmap, Dig/nslookup, WHOIS, curl, and vulnerability scanners) to map attack surfaces. Manual execution leads to:
- Inconsistent and unnormalized data formats across tools.
- Disconnected outputs without historical baseline tracking or change detection.
- Subjective risk assessments without clear policy traceability.
- Confusion between "no findings detected" and "collection tool failure".
- Operational friction when tracking vulnerability remediation or visualizing complex network topologies.

NetSecureLab addresses these challenges through a unified, 5-stage automated assessment pipeline:
1. **Unifying the Reconnaissance Pipeline**: Target Registration & Authorization &rarr; Network Discovery &rarr; Service/OS/NSE Enumeration &rarr; DNS Intelligence &rarr; Passive Recon &rarr; Rule-Based Analysis &rarr; Web Application Posture &rarr; Scan Comparison &rarr; Standalone Report.
2. **Normalizing Multi-Tool Outputs**: Storing structured asset snapshots, open ports, service banners, script outputs, and DNS records in a clean relational schema (`PRAGMA foreign_keys=ON`).
3. **Transparent, Evidence-Backed Rules**: 14 deterministic network/service/DNS rules (`R001`-`R014`) and 8 web application security rules (`WEB-001`-`WEB-007-GIT`) with complete rule ID traceability and evidence samples.
4. **Independent Module Outcome Tracking**: Explicitly records whether Nmap, DNS, or Recon succeeded, degraded, or failed (`nmap_status`, `dns_status`, `recon_status`).
5. **Technical Authorization Controls**: Backend-enforced authorization verification before any scan can execute; unauthorized scan attempts are rejected with HTTP 403.
6. **Live Observability & Visualization**: WebSocket scan event streaming (`/ws/scans`), interactive SVG network topology visualization (`/topology`), and ASGI request correlation tracking (`X-Request-ID`).
7. **Enterprise Risk Management**: Target recurring schedules, finding remediation lifecycle tracking (`open`, `acknowledged`, `accepted_risk`, `remediated`), analyst notes, and machine-readable CSV/JSON exports.

---

## 2. Key Capabilities & Modern Extensions

### Core Pipeline Capabilities
- **Canonical Target Normalization**: Centralized `TargetNormalizer` transforms IP addresses, hostnames, domains, and web application URLs into canonical forms for downstream modules.
- **Backend-Controlled Scan Profiles**:
  - `Quick`: Fast host discovery only (`-sn`).
  - `Standard`: TCP port scanning of top 1,000 ports with service version detection (`-sV -T4`).
  - `Full`: Full port sweep (`-sV -sC -T4 -p-`) with decoupled, non-fatal OS detection pass (`-O`) and targeted NSE scripts.
- **Subprocess Safety**: Command arguments are built strictly as lists executed with `shell=False` and enforced timeouts (`MAX_SCAN_TIMEOUT = 1800s`). Shell injection metacharacters are strictly validated and rejected.
- **Independent Collection Modules**: Failure or timeout in Nmap does not block DNS intelligence or WHOIS passive reconnaissance.
- **Module-Aware Finding Engine**: Skips port-based rules if Nmap failed, preventing misleading "clean" reports.
- **Cooperative Cancellation & Crash Recovery**: Checks `cancel_requested` between pipeline stages to halt execution gracefully. On startup, stale `queued`/`running` scans are automatically recovered and marked `failed` with descriptive messages.
- **Historical Comparison**: Direct diffing of normalized snapshots across scans of the same target (identifying added/removed hosts, open ports, service version updates, and resolved findings).

### Modern Enterprise Extensions
- **Interactive Network Topology Visualization**: Live interactive SVG topology graph (`/topology`) rendering relational hierarchies: `Targets &rarr; Discovered Hosts &rarr; Exposed Services &rarr; Security Findings`. Includes pan, zoom, search filter, node type toggles, and side inspector drawer.
- **Automated Web Application Security Assessment**: Automated HTTP/HTTPS scanner (`source="zap"`, rules `WEB-001` through `WEB-007-GIT`) evaluating HSTS, CSP, X-Frame-Options clickjacking protection, MIME-sniffing, server technology banners, cookie security flags (`Secure`, `HttpOnly`), and sensitive path disclosure (`.env`, `.git/HEAD`).
- **Nmap NSE Script Parsing & Analysis**: Extracts XML `<script>` outputs to detect weak cryptographic cipher suites (SSLv2, SSLv3, TLS 1.0, RC4, 3DES via `R013`) and dangerous HTTP methods (`PUT`, `DELETE`, `TRACE` via `R014`).
- **Real-Time Observability**: WebSocket scan event streaming (`/ws/scans`) with automatic polling fallback in the React frontend, ASGI `RequestCorrelationMiddleware` injecting `X-Request-ID` and execution latency headers, and context-aware structured logging.
- **Automated Scan Scheduling**: Configurable recurring scan schedules (`daily`, `weekly`, `monthly`) powered by a background scheduler worker (`scheduler.py`) with UI modal controls on target detail pages.
- **Finding Lifecycle & Remediation Workflow**: Track finding remediation status (`open`, `acknowledged`, `accepted_risk`, `remediated`) with analyst notes drawer and live updates via `PATCH /findings/{id}`.
- **Machine-Readable Exports**: One-click exports of findings to **CSV** (`/findings/export/csv`) and **JSON** (`/findings/export/json`) for SIEM and ticketing integration.
- **Role-Based Access Control (RBAC) & Authentication**: JWT bearer tokens (`/auth/login`, `/auth/me`, `/auth/register`), bcrypt password hashing, operator and administrator privileges, with automatic default admin seeding.
- **Print-to-PDF Reports**: HTML reports include styled CSS print media queries and an instant browser print trigger for clean PDF output.

---

## 3. Architecture Overview

```
                                  +------------------------------------------+
                                  |         React 18+ Single Page App        |
                                  |  (Dashboard, Targets, Topology, Reports) |
                                  +---------------------+--------------------+
                                                        |
                                +-----------------------+-----------------------+
                                | REST API (Axios)      | WebSockets (/ws/scans)|
                                v                       v                       v
     +---------------------------------------------------------------------------------+
     |                               FastAPI Application                               |
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

## 4. Technology Stack

| Layer | Technology | Usage / Rationale |
|---|---|---|
| **Frontend Framework** | React 18+ / Vite | High-performance SPA with fast HMR |
| **Frontend Routing** | React Router v6 | Single-Page Application routing |
| **Styling** | Vanilla CSS Modules | Glassmorphism, CSS tokens, responsive dark theme |
| **HTTP Client** | Axios | Interceptors with auth tokens & global error handling |
| **Real-Time Client** | Native WebSocket | Auto-reconnecting `/ws/scans` event streaming with polling fallback |
| **Backend Framework** | Python 3.11+ / FastAPI | Async endpoints, Pydantic v2 schemas, OpenAPI auto-docs |
| **Authentication & RBAC**| PyJWT & Passlib (Bcrypt)| Cryptographic bearer tokens, hashed passwords, role-based guards |
| **ORM & Database** | SQLAlchemy 2.0 / SQLite | Relational schema, SQLite PRAGMA FK enforcement, auto-migrations |
| **Job Execution** | `ThreadPoolExecutor` & Thread | Non-blocking scan worker & recurring cron scheduler |
| **Network Scanning** | Nmap + `xml.etree.ElementTree` | Subprocess execution, native XML parsing, NSE script analysis |
| **Web Assessment** | `httpx` (Async/Sync HTTP Client) | ZAP-compatible security posture checks (HSTS, CSP, Cookies, Headers) |
| **DNS Intelligence** | `dnspython` | A, AAAA, MX, NS, TXT, and `_dmarc.<domain>` queries |
| **Passive Recon** | `python-whois` + `socket` | Domain registrar lookup, reverse DNS resolution |
| **Reporting Engine** | Jinja2 | Standalone HTML reports with print-to-PDF media styles |
| **Containerization** | Docker & Docker Compose | Multi-stage production images with Nginx reverse proxy |
| **Testing & Quality** | pytest (34 tests), Vitest (10 tests), Oxlint | Full test coverage (100% pass) and zero linter warnings |

---

## 5. Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher (Node 20+ recommended)
- Nmap installed and in system PATH (e.g., `nmap --version`)
  - *Windows*: Download from [nmap.org](https://nmap.org/download.html) or `winget install Insecure.Nmap`
  - *Linux*: `sudo apt update && sudo apt install -y nmap`
  - *macOS*: `brew install nmap`

### Backend Installation

```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### Frontend Installation

```bash
cd frontend
npm install
```

---

## 6. Running the Application

### Option A: Docker & Docker Compose (Recommended)

NetSecureLab includes production-ready Docker containers with Nmap pre-installed and Nginx configured as a reverse proxy:

```bash
# Build and launch both backend and frontend containers
docker compose up --build -d
```

- **Web Dashboard**: [http://localhost:3000](http://localhost:3000)
- **API Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

View live container logs:
```bash
docker compose logs -f
```

Stop containers:
```bash
docker compose down
```

---

### Option B: Running Locally without Docker

> **Important**: Ensure Nmap is installed and available in your PATH. NetSecureLab runs as a **single Uvicorn worker** because scan orchestration uses an in-process thread pool.

#### 1. Start the Backend API Server

```bash
cd backend
# Ensure virtual environment is activated:
uvicorn app.main:app --reload --port 8000
```
Swagger UI documentation will be live at: `http://localhost:8000/docs`

#### 2. Start the Frontend Development Server

```bash
cd frontend
npm run dev
```
Open your browser to: `http://localhost:5173`

---

## 7. Default Credentials

On application startup, NetSecureLab automatically initializes the database schema, performs stale scan crash recovery, and seeds an initial administrator account if no users exist:

| Username | Password | Role | Description |
|---|---|---|---|
| `admin` | `NetSecureLab#2026!` | `admin` | Primary administrative user with user registration privileges |

Authentication tokens can be obtained via `POST /auth/login` or via the web application login modal.

---

## 8. API Reference

### Authentication & RBAC
- `POST /auth/login`: Authenticate credentials, returns signed JWT bearer token and user profile.
- `GET /auth/me`: Retrieve current authenticated user profile (`operator` or `admin`).
- `POST /auth/register`: Create a new user account (requires `admin` role).

### Targets & Scheduling
- `POST /targets`: Register a new target. Requires `authorization_confirmed: true`.
- `GET /targets`: List all registered targets with scan counts.
- `GET /targets/{id}`: Retrieve detailed target profile.
- `PATCH /targets/{id}/schedule`: Configure recurring scan schedule (`interval`: `daily`, `weekly`, `monthly`, or `none`; `profile`: `quick`, `standard`, `full`).
- `DELETE /targets/{id}`: Delete target (returns HTTP 409 conflict if associated scans exist).

### Scans & Execution
- `POST /scans`: Create and queue scan (`{target_id, profile}`). Rejects unauthorized targets (HTTP 403) and duplicate active scans on the same target (HTTP 409).
- `GET /scans`: List all scans. Filterable by `target_id`.
- `GET /scans/{id}`: Detailed scan status and module outcome summaries.
- `GET /scans/{id}/status`: Lightweight status endpoint for UI polling fallback.
- `POST /scans/{id}/cancel`: Request cooperative scan cancellation.
- `GET /scans/{id}/hosts`: Discovered host snapshots.
- `GET /scans/{id}/ports`: Discovered open/filtered ports and service banners.
- `GET /scans/{id}/services`: Distinct services enumerated.
- `GET /scans/{id}/dns`: Collected DNS records.
- `GET /scans/{id}/recon`: Passive reconnaissance results (WHOIS, reverse DNS).
- `GET /scans/{id}/raw`: Secure download of raw Nmap XML output.
- `GET /scans/compare/{scan1}/{scan2}`: Comparative diff of two scans on the same target.

### Findings & Remediation Lifecycle
- `GET /findings`: All findings across scans. Filterable by `severity`, `category`, and `source`.
- `GET /scans/{id}/findings`: Findings detected in a specific scan.
- `PATCH /findings/{id}`: Update remediation status (`open`, `acknowledged`, `accepted_risk`, `remediated`) and analyst investigation notes.
- `GET /findings/export/csv`: Export all findings matching filters as a downloadable CSV.
- `GET /findings/export/json`: Export all findings matching filters as a formatted JSON payload.

### Network Topology
- `GET /topology`: Retrieve full network graph (nodes and links) representing `Targets &rarr; Discovered Hosts &rarr; Exposed Ports &rarr; Vulnerability Findings`, with optional `target_id` filter.

### Reports & Dashboard
- `POST /reports/{scan_id}/generate`: Generate HTML assessment report (`compare_with` optional).
- `GET /reports/{scan_id}`: View rendered HTML report.
- `GET /reports/{scan_id}/download`: Download HTML report file.
- `GET /dashboard/stats`: Global aggregated metrics (targets, scans, assets, severity counts).
- `GET /health`: System health and version status.

### Real-Time WebSockets
- `WebSocket /ws/scans`: Live streaming connection broadcasting scan state transitions (`scan_status`, duration, module outcomes).

---

## 9. Security Rules Catalog

NetSecureLab applies transparent, evidence-backed security checks. Findings describe **observed facts** and **recommend administrative review**; they do not claim unverified exploits.

### Network & Infrastructure Rules (Source: `nmap` & `dns`)

| Rule ID | Title | Condition | Severity | Category | Source |
|---|---|---|---|---|---|
| `R001` | FTP Service Reachable | TCP/21 open | Medium | Service Exposure | `nmap` |
| `R002` | Telnet Service Reachable | TCP/23 open | Medium | Service Exposure | `nmap` |
| `R003` | Database Service Reachable | TCP 3306/5432/1433/1521/27017 open | Medium | Service Exposure | `nmap` |
| `R004` | SMB/NetBIOS Service Reachable | TCP 139/445 open | Medium | Service Exposure | `nmap` |
| `R005` | RDP Service Reachable | TCP/3389 open | Low | Service Exposure | `nmap` |
| `R006` | Web Service Detected | TCP 80/443/8080/8443 open with HTTP | Informational | Web Discovery | `nmap` |
| `R007` | SSH Service Detected | TCP/22 open | Informational | Service Info | `nmap` |
| `R008` | Service Version Identified | Version string extracted by banner grab | Informational | Fingerprinting | `nmap` |
| `R009` | OS Fingerprint Identified | OS signature detected via TCP/IP stack | Informational | Fingerprinting | `nmap` |
| `R010` | SPF Record Not Found | Missing `v=spf1` TXT record (domain targets) | Low | DNS Security | `dns` |
| `R011` | DMARC Record Not Found | Missing `v=DMARC1` TXT record at `_dmarc.<domain>` | Low | DNS Security | `dns` |
| `R012` | Multiple MX Servers | Multiple MX records detected | Informational | Mail Infrastructure | `dns` |
| `R013` | Insecure SSL/TLS or Weak Cipher Suites | Obsolete protocols/ciphers in NSE output | Medium | Cryptographic Security | `nmap` |
| `R014` | Dangerous HTTP Methods Enabled | Risky methods (PUT, DELETE, TRACE) in NSE | Low | Web Security | `nmap` |

### Web Application Posture Rules (Source: `zap`)

| Rule ID | Title | Condition | Severity | Category | Source |
|---|---|---|---|---|---|
| `WEB-001` | Missing HSTS Header | HTTPS endpoint missing `Strict-Transport-Security` | Medium | Web Security | `zap` |
| `WEB-001-HTTP` | Unencrypted HTTP In Use | Cleartext HTTP web service endpoint active | Medium | Web Security | `zap` |
| `WEB-002` | Missing Content Security Policy | Missing `Content-Security-Policy` header | Medium | Web Security | `zap` |
| `WEB-003` | Missing Clickjacking Protection | Missing `X-Frame-Options` and CSP `frame-ancestors`| Medium | Web Security | `zap` |
| `WEB-004` | Missing MIME-Sniffing Protection | Missing `X-Content-Type-Options: nosniff` | Low | Web Security | `zap` |
| `WEB-005` | Server / Framework Version Disclosure | Disclosed `Server` or `X-Powered-By` banners | Informational | Information Disclosure | `zap` |
| `WEB-006` | Insecure Cookie Flags | Session cookies missing `Secure` or `HttpOnly` | Low | Web Security | `zap` |
| `WEB-007` | Exposed `.env` Configuration File | Publicly accessible `.env` configuration file | High | Sensitive Data Exposure| `zap` |
| `WEB-007-GIT` | Exposed `.git` Repository Metadata | Publicly accessible `.git/HEAD` metadata | High | Sensitive Data Exposure| `zap` |

---

## 10. Automated Testing & Code Quality

### Backend Test Suite (34 Pytest Tests - 100% Pass)
```bash
cd backend
.venv\Scripts\python.exe -m pytest -v
```
The backend test suite covers:
- **Authentication & RBAC**: Password hashing, JWT token issue/validation, admin registration guards, unauthorized access rejection.
- **Target Validation**: Canonical normalization, IP, domain, URL validation, and shell injection rejection.
- **Technical Authorization Control**: Backend rejection (HTTP 403) on unconfirmed targets.
- **Target Integrity**: Protection against deleting targets with associated scan records (HTTP 409).
- **Concurrency Guard**: Rejection of concurrent active scans on the same target (HTTP 409).
- **Nmap XML & NSE Parsing**: Extracting hosts, ports, banners, and NSE script outputs from XML fixtures.
- **Module Independence**: Ensuring DNS and Recon succeed even if Nmap fails or times out.
- **Cooperative Cancellation**: Verifying scan termination between execution stages.
- **Rule Finding Engine**: Validating triggers for `R001`-`R014` and module-awareness skipping.
- **Web Security Scanner**: Verifying posture evaluation (HSTS, CSP, cookies, sensitive files) with `source="zap"`.
- **Scan Comparison Engine**: Calculating deltas for added/removed hosts, ports, and version changes.
- **Network Topology API**: Validating node and link graph construction and summary statistics.
- **Automated Scheduler**: Triggering overdue recurring scans and calculating next execution times.
- **Crash Recovery**: Automatic startup recovery of orphaned `running`/`queued` scans.

### Frontend Test Suite (10 Vitest Tests - 100% Pass)
```bash
cd frontend
npm test
```
The frontend test suite verifies:
- Badge component rendering for all status and severity variants (`critical`, `high`, `medium`, `low`, `informational`).
- Modal component interactions, focus management, and keyboard dismissal.

### Static Analysis & Linting (0 Warnings, 0 Errors)
```bash
cd frontend
npx oxlint
```
NetSecureLab maintains zero warnings and zero errors across all React components and utility modules.

---

## 11. Technical Controls & Ethical Scope

NetSecureLab is engineered strictly for authorized security assessments in controlled laboratory environments:
1. **Mandatory Authorization Confirmation**: Targets require explicit authorization confirmation in the database (`authorization_confirmed = True`) before any scan can execute. Unauthorized targets are rejected with HTTP 403.
2. **Backend-Controlled Profiles**: Scans execute only predefined profiles; arbitrary Nmap command strings cannot be injected via the API or UI.
3. **Subprocess Isolation**: Commands are invoked strictly via list arguments with `shell=False` and enforced timeouts (`MAX_SCAN_TIMEOUT = 1800s`).
4. **Historical Preservation**: Targets with historical scan records cannot be deleted (HTTP 409 Conflict), preserving auditability and comparison integrity.
5. **No Destructive Exploits**: The framework explicitly excludes automated exploitation, credential brute-forcing, Denial of Service (DoS), or unauthenticated web crawling.

---

## 12. Limitations & Methodology Scope

- **Fact vs. Vulnerability Distinction**: Findings report exposed services, observed headers, and configuration facts. Reachability of a database port or web service indicates potential attack surface, not an exploited flaw.
- **Port Scope Boundaries**: Scans only inspect ports specified in the active scan profile. Filtered or unprobed ports may host uninspected services.
- **Passive Intelligence Degradation**: WHOIS and public DNS resolution depend upon external registry servers; network dropouts degrade these modules gracefully to `partial` or `skipped`.
- **Single Lab Worker**: The background task runner is configured with `max_workers=1` to guarantee reliable operation in resource-constrained lab environments without saturating host network adapters.

---

## 13. License & Course Attribution

Developed as an academic reference implementation demonstrating the integration of Computer Networks and Ethical Hacking laboratory concepts.

**Primary Course Alignment**:
- Computer Networks (IP addressing, TCP/UDP transport layer, DNS resolution, mail routing)
- Ethical Hacking (Passive reconnaissance, active scanning, fingerprinting, web application security posture, transparent rule-based risk evaluation)