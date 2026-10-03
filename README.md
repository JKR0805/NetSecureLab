# NetSecureLab (v2.1)
### Integrated Network Security Assessment & Reconnaissance Framework

NetSecureLab is an integrated network security assessment and reconnaissance framework developed for authorized laboratory environments. It combines active network discovery, service enumeration, DNS intelligence, passive reconnaissance, and rule-based security policy checks into a single automated pipeline with historical scan comparison and standalone reporting.

---

## Table of Contents

1. [Overview & Problem Statement](#overview--problem-statement)
2. [Key Capabilities & Features](#key-capabilities--features)
3. [Architecture Overview](#architecture-overview)
4. [Technology Stack](#technology-stack)
5. [Installation & Setup](#installation--setup)
6. [Running the Application](#running-the-application)
7. [API Reference](#api-reference)
8. [Security Rules Catalog](#security-rules-catalog)
9. [Automated Testing](#automated-testing)
10. [Technical Controls & Ethical Scope](#technical-controls--ethical-scope)
11. [Limitations & Methodology Scope](#limitations--methodology-scope)

---

## 1. Overview & Problem Statement

Network administrators and security engineers often rely on disparate command-line tools (Nmap, Dig/nslookup, WHOIS, curl) to map attack surfaces. Manual execution leads to:
- Inconsistent and unnormalized data formats.
- Disconnected outputs without historical baseline tracking.
- Subjective risk assessments without clear policy traceability.
- Confusion between "no findings detected" and "collection tool failure".

NetSecureLab addresses these challenges by:
1. **Unifying the reconnaissance pipeline**: Target → Discover → Enumerate → Analyze → Findings → Compare → Report.
2. **Normalizing tool outputs**: Storing structured asset snapshots, open ports, and DNS records in a clean relational schema.
3. **Transparent, evidence-backed rules**: 12 deterministic rules with rule ID traceability (`R001`-`R012`).
4. **Independent module outcome tracking**: Explicitly records whether Nmap, DNS, or Recon succeeded, degraded, or failed.
5. **Technical authorization controls**: Backend-enforced authorization checkbox requirement before any scan can run.
6. **Scan-to-scan comparison**: Detects added/removed hosts, open ports, service version updates, and resolved findings between snapshots.
7. **Standalone assessment reporting**: Generates structured HTML reports including scope, findings, and explicit limitation disclaimers.

---

## 2. Key Capabilities & Features

- **Canonical Target Normalization**: Centralized `TargetNormalizer` transforms IP addresses, hostnames, domains, and web application URLs into canonical forms for downstream modules.
- **Backend-Controlled Scan Profiles**:
  - `Quick`: Fast host discovery only (`-sn`).
  - `Standard`: TCP port scanning of top 1,000 ports with service version detection (`-sV -T4`).
  - `Full`: Full port sweep (`-sV -sC -T4 -p-`) with a decoupled, non-fatal OS detection pass (`-O`).
- **Subprocess Safety**: Command arguments are built strictly as lists executed with `shell=False` and enforced timeouts. User input is validated against shell injection metacharacters.
- **Independent Collection Modules**: Failure of Nmap does not block DNS intelligence or WHOIS passive reconnaissance.
- **Module-Aware Finding Engine**: Skips port-based rules if Nmap failed, preventing misleading "clean" reports.
- **Cooperative Cancellation**: Checks `cancel_requested` between pipeline stages to halt execution gracefully.
- **Crash Recovery**: Automatically marks stale `queued`/`running` scans as `failed` on application startup with clear explanatory messages.
- **Historical Comparison**: Direct diffing of normalized snapshots across scans of the same target.

---

## 3. Architecture Overview

```
                      React + Vite SPA
                             |
                             | REST API (Axios)
                             v
                    FastAPI Application
                             |
               +-------------+-------------+
               |                           |
               v                           v
         API Controllers           Scan Worker Thread
         (FastAPI / Pydantic)      (ThreadPoolExecutor max_workers=1)
                                           |
                                   Scan Orchestrator
                                           |
                     +---------------------+--------------------+
                     |                     |                    |
                     v                     v                    v
                  Nmap                    DNS                 Recon
               (subprocess)           (dnspython)         (whois/optional)
                     |                     |                    |
                     +---------------------+--------------------+
                                           |
                                           v
                                SQLite Normalized Store
                                (PRAGMA foreign_keys=ON)
                                           |
                                           v
                                 Rule Finding Engine
                                           |
                          +----------------+----------------+
                          |                                 |
                          v                                 v
                   Dashboard / UI                     Report Engine
                          |                         (Jinja2 Template)
                          v
                   Scan Comparison
```

---

## 4. Technology Stack

| Layer | Technology | Usage / Rationale |
|---|---|---|
| **Frontend Framework** | React 18+ / Vite | Fast HMR, component architecture |
| **Frontend Routing** | React Router v6 | Single-Page Application routing |
| **Styling** | Vanilla CSS Modules | Scoped styles, custom properties, glassmorphism |
| **HTTP Client** | Axios | Interceptors for global error handling |
| **Backend Framework** | Python 3.11+ / FastAPI | OpenAPI auto-docs, asynchronous endpoints |
| **ORM** | SQLAlchemy 2.0 (Sync) | Relational mapping, SQLite PRAGMA FK enforcement |
| **Database** | SQLite | Zero-configuration local database |
| **Job Execution** | `ThreadPoolExecutor(max_workers=1)` | Single-worker lab orchestrator |
| **Network Scanning** | Nmap + `xml.etree.ElementTree` | Direct subprocess execution and native XML parsing |
| **DNS Intelligence** | `dnspython` | A, AAAA, MX, NS, TXT, and `_dmarc.<domain>` queries |
| **Passive Recon** | `python-whois` + `socket` | Optional domain registry enrichment & reverse DNS |
| **Reporting** | Jinja2 | Standalone HTML assessment report generation |
| **Testing** | pytest (Backend), Vitest (Frontend) | Unit, integration, and UI testing |

---

## 5. Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher (Node 20+ recommended)
- Nmap installed and available in system PATH (e.g. `nmap --version`)
  - *Windows*: Download from [nmap.org](https://nmap.org/download.html) or `winget install Insecure.Nmap`
  - *Linux*: `sudo apt install nmap`
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

### Option A: Running with Docker & Docker Compose (Recommended)

NetSecureLab includes production-ready Docker containers with Nmap pre-installed and configured:

```bash
# Build and launch both backend and frontend containers in the background
docker compose up --build -d
```

- **Web Dashboard**: [http://localhost:3000](http://localhost:3000)
- **API Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

To view logs:
```bash
docker compose logs -f
```

To stop containers:
```bash
docker compose down
```

---

### Option B: Running Locally without Docker

> **Important**: When running without Docker, ensure Nmap is installed on the host machine. NetSecureLab is designed for a **single Uvicorn worker** because scan orchestration uses an in-process thread pool.

#### 1. Start the Backend API Server

```bash
cd backend
# With virtual environment activated:
uvicorn app.main:app --reload --port 8000
```
API Documentation (Swagger UI) is available at: `http://localhost:8000/docs`

#### 2. Start the Frontend Development Server

```bash
cd frontend
npm run dev
```
Access the web application at: `http://localhost:5173`

---

## 7. API Reference

### Targets
- `POST /targets`: Register a new target. Requires `authorization_confirmed: true`.
- `GET /targets`: List all registered targets with scan counts.
- `GET /targets/{id}`: Retrieve detailed target profile.
- `DELETE /targets/{id}`: Delete target (returns HTTP 409 if associated scans exist).

### Scans & Results
- `POST /scans`: Create and queue scan (`{target_id, profile}`). Rejects unauthorized targets (HTTP 403).
- `GET /scans`: List all scans. Filterable by `target_id`.
- `GET /scans/{id}`: Get scan status and module outcome summaries.
- `GET /scans/{id}/status`: Lightweight status endpoint for UI polling.
- `POST /scans/{id}/cancel`: Request cooperative cancellation.
- `GET /scans/{id}/hosts`: Discovered host snapshots.
- `GET /scans/{id}/ports`: Discovered open/filtered ports.
- `GET /scans/{id}/services`: Distinct services enumerated.
- `GET /scans/{id}/dns`: Collected DNS records.
- `GET /scans/{id}/recon`: Passive reconnaissance results.
- `GET /scans/{id}/raw`: Secure download of raw Nmap XML.
- `GET /scans/compare/{scan1}/{scan2}`: Comparative diff of two scans.

### Findings & Reports
- `GET /findings`: All findings across scans. Filterable by `severity`, `category`, and `source`.
- `GET /scans/{id}/findings`: Findings for a specific scan.
- `POST /reports/{scan_id}/generate`: Generate HTML report (`compare_with` optional).
- `GET /reports/{scan_id}`: View rendered HTML report.
- `GET /reports/{scan_id}/download`: Download HTML report file.
- `GET /dashboard/stats`: Global aggregated metrics.

---

## 8. Security Rules Catalog

Findings describe **observed facts** and **recommend administrative review**. They do not claim to identify unverified vulnerabilities.

| Rule ID | Title | Condition | Severity | Category |
|---|---|---|---|---|
| `R001` | FTP Service Reachable | TCP/21 open | Medium | Service Exposure |
| `R002` | Telnet Service Reachable | TCP/23 open | Medium | Service Exposure |
| `R003` | Database Service Reachable | TCP 3306/5432/1433/1521/27017 open | Medium | Service Exposure |
| `R004` | SMB/NetBIOS Service Reachable | TCP 139/445 open | Medium | Service Exposure |
| `R005` | RDP Service Reachable | TCP/3389 open | Low | Service Exposure |
| `R006` | Web Service Detected | TCP 80/443/8080/8443 open with HTTP | Informational | Web Discovery |
| `R007` | SSH Service Detected | TCP/22 open | Informational | Service Info |
| `R008` | Service Version Identified | Version string extracted by banner grab | Informational | Fingerprinting |
| `R009` | OS Fingerprint Identified | OS detection returned signature | Informational | Fingerprinting |
| `R010` | SPF Record Not Found | No TXT record starting with `v=spf1` (domain targets) | Low | DNS Security |
| `R011` | DMARC Record Not Found | No TXT record at `_dmarc.<domain>` (domain targets) | Low | DNS Security |
| `R012` | Multiple MX Servers | More than one MX record detected (domain targets) | Informational | Mail Infrastructure |

---

## 9. Automated Testing

### Backend Unit & Integration Tests (pytest)
```bash
cd backend
python -m pytest -v
```
Test suite verifies:
- Target validation (IP, domain, URL, shell injection rejection).
- Technical authorization enforcement (HTTP 403 on unauthorized scans).
- Target deletion protection (HTTP 409 conflict when scans exist).
- Nmap XML parsing against sample fixtures.
- Module independence (DNS succeeds even if Nmap fails).
- Cooperative scan cancellation between stages.
- Finding engine rule triggers and module-awareness skipping.
- Snapshot comparison delta calculations.
- Stale scan recovery on application restart.
- Jinja2 report compilation.

### Frontend Component Tests (Vitest)
```bash
cd frontend
npm test
```

---

## 10. Technical Controls & Ethical Scope

NetSecureLab is designed strictly for authorized security assessments in educational and controlled laboratory environments:
1. **Mandatory Authorization Confirmation**: Targets require an explicit technical confirmation before scanning can be executed. Unconfirmed targets are rejected with HTTP 403.
2. **Backend-Controlled Profiles**: Users cannot submit arbitrary Nmap command strings, preventing command injection attacks.
3. **Cooperative Cancellation**: Running jobs can be cancelled between execution stages.
4. **Historical Preservation**: Targets with scan history cannot be deleted, ensuring accountability and comparison integrity.

---

## 11. Limitations & Methodology Scope

- **Fact vs. Vulnerability Distinction**: Findings report exposed services and configuration facts. Reachability of a database port or FTP service does not constitute an exploited vulnerability.
- **Port Scope Boundaries**: Scans only probe the port ranges defined in the selected profile. Filtered or unprobed ports may harbor uninspected services.
- **Passive Intelligence Degradation**: WHOIS and public DNS resolution depend upon external registry servers; network dropouts degrade these modules gracefully to `partial` or `skipped`.

---

## License

Developed for Authorized Laboratory Assessment & Educational Use.