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

## 3.1 Core Scope

The core implementation should contain:

1. Target management
2. Scan management
3. Nmap host discovery
4. Port scanning
5. Service/version detection
6. Optional OS detection
7. DNS record enumeration
8. Basic passive reconnaissance
9. Result normalization
10. Rule-based finding generation
11. Findings dashboard
12. Scan history
13. Scan comparison
14. Security assessment report

## 3.2 Optional Extension

Add only after the core system is stable:

15. OWASP ZAP integration for authorized local web targets
16. Selected Nmap NSE results
17. Network topology visualization

## 3.3 Explicitly Out of Scope

Do not make the core project depend on:

- Autonomous exploitation
- Automated attack execution
- Credential theft
- Malware
- Real-time enterprise IDS
- Autonomous penetration testing
- ML-based threat prediction
- LLM-based vulnerability analysis
- Large enterprise compliance engines
- Multi-vendor configuration auditing
- Large-scale threat-intelligence aggregation
- Unrestricted Internet scanning

The project should operate on systems for which the tester has explicit authorization.

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
                         NETSECURELAB
                              |
                              v
                      React Frontend
                              |
                           REST API
                              |
                              v
                         FastAPI Backend
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
      Nmap Adapter        DNS Adapter        Recon Adapter
          |                   |                   |
          v                   v                   v
        Nmap            DNS libraries /       Passive
                        system utilities     information
          |                   |                   |
          +-------------------+-------------------+
                              |
                              v
                       Result Normalizer
                              |
                              v
                       Finding Rule Engine
                              |
                 +------------+------------+
                 |                         |
                 v                         v
            SQLite Database          Scan Comparison
                 |
                 v
            Report Generator
```

Optional extension:

```text
Web Target
    |
    v
OWASP ZAP
    |
    v
ZAP Adapter
    |
    v
Common Finding Model
```

---

# 6. Recommended Technology Stack

## Frontend
- React
- Vite
- Standard CSS / CSS modules / existing preferred styling solution
- Optional chart library only where a chart adds analytical value

## Backend
- Python
- FastAPI
- Pydantic
- Python standard library where practical

## Database
- SQLite for the initial application
- SQLAlchemy or another lightweight ORM if useful

## Network/Security Tools
- Nmap
- Optional OWASP ZAP
- DNS utilities / Python DNS library
- WHOIS/RDAP-compatible source where available

## Reporting
- HTML report as the minimum
- PDF generation as an enhancement

## Development Environment
- Kali Linux or Linux VM for security tooling
- Windows development is acceptable if the required security tools are available

---

# 7. Module 1: Target Management

## Purpose

Create and maintain targets that are explicitly authorized for assessment.

## Target Types

At minimum:

- IP address
- Hostname
- Domain
- Web URL

## Target fields

```text
Target
------
id
name
target
target_type
description
created_at
```

## Example

```text
Name: College Lab VM
Target: 192.168.56.101
Type: IP
```

or:

```text
Name: Local Juice Shop
Target: http://192.168.56.102:3000
Type: Web Application
```

## UI

```text
Targets

[ + Add Target ]

Target Name
Target
Target Type
Description

[Save]
```

Include an authorization notice:

> Scan only systems and applications for which explicit permission has been obtained.

---

# 8. Module 2: Scan Management

## Scan Profiles

Keep a small number of understandable presets.

### Quick Scan
- Host discovery
- Basic port scan

### Standard Scan
- Host discovery
- Port scan
- Service/version detection

### Full Assessment
- Host discovery
- Port scan
- Service/version detection
- OS detection
- Selected NSE scripts

The exact command-line options should be centralized in the backend and not hard-coded across frontend components.

## Scan lifecycle

```text
Created
   |
   v
Queued / Started
   |
   v
Running
   |
   +----> Failed
   |
   v
Completed
```

## Scan record

```text
Scan
----
id
target_id
profile
status
started_at
completed_at
duration
raw_output_path
error_message
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

Different tools produce different formats.

The backend should normalize them into common entities.

## Asset

```text
Asset
-----
id
scan_id
ip
hostname
status
os
discovered_at
```

## Port

```text
Port
----
id
asset_id
port_number
protocol
state
service
product
version
extra_info
```

## DNS record

```text
DNSRecord
---------
id
target_id
record_type
name
value
ttl
```

## Recon result

```text
ReconResult
-----------
id
target_id
category
key
value
source
collected_at
```

## Finding

```text
Finding
-------
id
scan_id
asset_id
category
title
description
severity
evidence
source
recommendation
created_at
```

---

# 13. Module 7: Rule-Based Finding Engine

The finding engine should initially be deterministic and transparent.

## Why rule-based?

- Easy to explain in a viva
- Easy to test
- Easy to reproduce
- Easy to justify
- Does not require a training dataset
- Keeps the project aligned with networking/security rather than turning it into an ML project

## Conceptual flow

```text
Normalized Results
       |
       v
Security Rules
       |
       v
Findings
```

## Example checks

### Exposed FTP service

```text
IF TCP port 21 is open
THEN:
    finding_type = service_exposure
    title = Exposed FTP Service
```

### Exposed database service

```text
IF a database-related service is directly reachable
THEN:
    create a review/exposure finding
```

### HTTP service detected

```text
IF HTTP service is detected
THEN:
    mark web application as discovered
    optionally queue web assessment
```

### Version information present

```text
IF service version is identified
THEN:
    record version for assessment and reporting
```

The final rule set should be small, documented, and supported by evidence.

Do not claim that these rules identify all vulnerabilities.

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

Recommended navigation:

```text
Dashboard
Targets
Scans
Assets
DNS Intelligence
Findings
Reports
```

## Targets
- list targets
- add target
- target details
- scan target

## Scans
- previous scans
- status
- profile
- duration
- result summary

## Assets
- discovered hosts
- host details
- ports
- services

## DNS Intelligence
- domain records
- mail servers
- nameservers

## Findings
- findings list
- filters
- evidence
- recommendations

## Reports
- generate/view report
- report history

---

# 18. Module 9: Scan Comparison

This is a high-value feature because it turns the application into a monitoring/assessment system rather than a one-time scanner.

## Concept

```text
Scan 1
  +
Scan 2
  |
  v
Difference Engine
```

## Compare

- New hosts
- Removed hosts
- New ports
- Removed ports
- New services
- Removed services
- Service/version changes
- New findings
- Resolved findings

## Example

```text
SCAN COMPARISON

Target: 192.168.56.101

New:
+ 3306/TCP
  MySQL detected

Removed:
- None

Changed:
22/TCP OpenSSH version changed

Findings:
+ Exposed Database Service
```

The comparison should operate against normalized records.

---

# 19. Module 10: Reporting

Generate a structured security-assessment report.

## Report structure

```text
NETSECURELAB
Network Security Assessment Report

1. Assessment Overview
2. Target Information
3. Scan Information
4. Discovered Hosts
5. Open Ports
6. Service / Version Information
7. DNS Intelligence
8. Reconnaissance Findings
9. Security Findings
10. Evidence
11. Recommendations
12. Scan Comparison (if applicable)
13. Limitations
```

## Report principles

- Show timestamps
- Show the target
- Show the scan profile
- Distinguish observed results from recommendations
- Include evidence
- Include limitations
- Do not claim comprehensive vulnerability coverage

HTML output is sufficient for the core version. PDF generation is an enhancement.

---

# 20. Optional Web Security Module: OWASP ZAP

This module corresponds to the web-security/proxy component of the course.

It should remain optional to the core framework.

## Architecture

```text
Web Target
    |
    v
OWASP ZAP
    |
    v
ZAP API / automation
    |
    v
ZAP Adapter
    |
    v
Normalized Findings
    |
    v
Dashboard + Report
```

## Use case

Use a deliberately vulnerable local application such as a laboratory target.

Do not use arbitrary Internet websites.

## Possible data to import

- Alert title
- Risk level
- URL
- Parameter
- Evidence
- Description
- Recommendation
- Source = ZAP

Map imported ZAP findings into the same `Finding` model.

This allows the dashboard to show:

```text
Finding Source
--------------
Nmap
DNS
Recon
ZAP
```

without changing the frontend data model.

---

# 21. Suggested Backend API

Keep the API small.

## Targets

```text
POST   /targets
GET    /targets
GET    /targets/{id}
DELETE /targets/{id}
```

## Scans

```text
POST   /scans
GET    /scans
GET    /scans/{id}
GET    /scans/{id}/status
```

## Results

```text
GET /scans/{id}/hosts
GET /scans/{id}/ports
GET /scans/{id}/services
GET /scans/{id}/dns
GET /scans/{id}/findings
```

## Comparison

```text
GET /scans/compare/{scan1}/{scan2}
```

## Reports

```text
GET /reports/{scan_id}
```

Exact route naming can change as implementation evolves, but the separation of responsibilities should remain.

---

# 22. Suggested Repository Structure

```text
netsecurelab/
|
+-- frontend/
|   +-- src/
|       +-- components/
|       +-- pages/
|       +-- services/
|       +-- hooks/
|       +-- App.jsx
|       +-- main.jsx
|
+-- backend/
|   +-- app/
|       +-- main.py
|       +-- routes/
|       +-- models/
|       +-- schemas/
|       +-- services/
|       |   +-- nmap_service.py
|       |   +-- dns_service.py
|       |   +-- recon_service.py
|       |   +-- finding_engine.py
|       |   +-- comparison.py
|       |   +-- report_service.py
|       |   +-- zap_service.py        # optional
|       |
|       +-- database/
|
+-- reports/
+-- scans/
+-- docs/
+-- README.md
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

# 27. Functional Test Cases

The project should have explicit tests.

## Test 1: Target creation
Input a valid authorized target.

Expected:
- target saved
- target appears in target list

## Test 2: Invalid target
Provide malformed target input.

Expected:
- validation error
- scan not started

## Test 3: Host discovery
Run quick assessment.

Expected:
- host status recorded

## Test 4: Port discovery
Scan a controlled host with known open ports.

Expected:
- open ports appear in database and UI

## Test 5: Service detection
Run service/version detection.

Expected:
- service and version fields populated where detected

## Test 6: DNS
Query a controlled/known domain.

Expected:
- DNS records displayed

## Test 7: Finding engine
Use a test host exposing a rule-covered service.

Expected:
- corresponding finding generated

## Test 8: Scan comparison
Perform two scans with a known controlled change.

Expected:
- new/removed service or port detected

## Test 9: Report generation
Generate report from completed scan.

Expected:
- report contains target, scan details, results, findings and recommendations

## Test 10: Tool failure
Simulate unavailable tool or failed lookup.

Expected:
- scan status/error handled gracefully

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

# 39. Definition of Done

The project is complete when the following end-to-end workflow works reliably:

```text
Create target
      ↓
Start scan
      ↓
Nmap executes
      ↓
Results parsed
      ↓
Hosts / Ports / Services stored
      ↓
DNS / Recon results collected where applicable
      ↓
Findings generated
      ↓
Dashboard displays results
      ↓
Previous scan can be compared
      ↓
Assessment report can be generated
```

The system should also handle common failures without crashing.

Optional ZAP integration can be considered complete only when it imports findings into the same normalized `Finding` model and displays them through the existing dashboard/report pipeline.

---

# 40. Recommended Project Statement

Use the following wording for academic/project documents:

> **NetSecureLab is an integrated network security assessment and reconnaissance framework designed for authorized laboratory environments. The framework combines passive reconnaissance, DNS enumeration, Nmap-based host and service discovery, selected security checks, finding correlation, historical scan comparison, and structured reporting through a unified web interface. The system is designed to demonstrate the integration of Computer Networks and Ethical Hacking concepts covered in the laboratory syllabus.**

---

# 41. Source Basis

Primary project reference materials:

- **CNEH Lab Syllabus.pdf**
- **CN EH CBP TITLES SUGGESTED.pdf**

The CNEH syllabus is the primary authority for determining course alignment.

The suggested-title document is useful for identifying related project directions already considered, particularly:
- network diagnostic frameworks
- infrastructure discovery
- passive reconnaissance
- DNS enumeration
- Nmap scanning
- vulnerability assessment

Current cybersecurity hackathon problem statements may be used for **context and inspiration**, but they do not override the course syllabus or the project's defined scope.

---

# 42. Core Principle

The final system should communicate one idea clearly:

```text
Network Discovery
       +
Reconnaissance
       +
Enumeration
       +
Security Assessment
       +
Historical Comparison
       +
Reporting
       =
NetSecureLab
```

The project is strongest when it is presented as a **course-aligned integrated framework**, not as an attempt to create a full commercial penetration-testing platform.
