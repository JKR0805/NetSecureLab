FROM python:3.12-slim

# Install system dependencies: Nmap, WHOIS, curl for healthcheck, and certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    whois \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app

# Create directories for persistent database, XML scans, and generated reports
RUN mkdir -p /app/data /app/scans /app/reports

# Default environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_URL="sqlite:////app/data/netsecurelab.db" \
    SCANS_DIR="/app/scans" \
    REPORTS_DIR="/app/reports" \
    NMAP_PATH="nmap"

EXPOSE 8000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Execute single-worker Uvicorn per architectural specification
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
