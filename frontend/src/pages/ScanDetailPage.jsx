import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  Activity,
  Server,
  Network,
  Globe,
  Compass,
  AlertTriangle,
  GitCompare,
  Download,
  FileText,
  Ban,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Layers,
} from 'lucide-react';
import { scanService } from '../services/scanService';
import { reportService } from '../services/reportService';
import { useScanPolling } from '../hooks/useScanPolling';
import { StatusBadge, SeverityBadge } from '../components/common/Badge';
import { Loader, EmptyState } from '../components/common/Loader';
import { Modal } from '../components/common/Modal';
import styles from './ScanDetailPage.module.css';

export function ScanDetailPage() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';

  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hosts, setHosts] = useState([]);
  const [ports, setPorts] = useState([]);
  const [dnsRecords, setDnsRecords] = useState([]);
  const [reconData, setReconData] = useState([]);
  const [findings, setFindings] = useState([]);

  // Comparison State
  const [allTargetScans, setAllTargetScans] = useState([]);
  const [compareScanId, setCompareScanId] = useState(searchParams.get('with') || '');
  const [comparisonResult, setComparisonResult] = useState(null);
  const [comparing, setComparing] = useState(false);

  // Report State
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportUrl, setReportUrl] = useState('');

  const loadScanData = useCallback(async () => {
    try {
      const scanData = await scanService.getScan(id);
      setScan(scanData);

      // If completed, fetch related result data in parallel
      if (scanData.status === 'completed' || scanData.status === 'failed') {
        const [h, p, d, r, f] = await Promise.all([
          scanService.getScanHosts(id).catch(() => []),
          scanService.getScanPorts(id).catch(() => []),
          scanService.getScanDNS(id).catch(() => []),
          scanService.getScanRecon(id).catch(() => []),
          scanService.getScanFindings(id).catch(() => []),
        ]);
        setHosts(h);
        setPorts(p);
        setDnsRecords(d);
        setReconData(r);
        setFindings(f);

        // Fetch sibling scans of the same target for comparison
        if (scanData.target_id) {
          const siblingScans = await scanService.listScans(scanData.target_id).catch(() => []);
          const otherScans = siblingScans.filter((s) => s.id !== Number(id) && s.status === 'completed');
          setAllTargetScans(otherScans);
          if (otherScans.length > 0 && !compareScanId) {
            setCompareScanId(otherScans[0].id);
          }
        }
      }
    } catch (err) {
      console.error('Failed to load scan detail:', err);
    } finally {
      setLoading(false);
    }
  }, [id, compareScanId]);

  // Use scan polling hook to update automatically while queued or running
  const onStatusChange = useCallback((newStatus) => {
    setScan((prev) => (prev ? { ...prev, ...newStatus } : newStatus));
    if (newStatus.status === 'completed') {
      loadScanData();
    }
  }, [loadScanData]);

  const { isPolling } = useScanPolling(id, onStatusChange);

  useEffect(() => {
    loadScanData();
  }, [loadScanData]);

  const handleTabChange = (tabName) => {
    setSearchParams({ tab: tabName });
  };

  const handleCancelScan = async () => {
    try {
      await scanService.cancelScan(id);
      loadScanData();
    } catch (err) {
      console.error('Cancel scan failed:', err);
    }
  };

  const handleRunComparison = async () => {
    if (!compareScanId) return;
    try {
      setComparing(true);
      const res = await scanService.compareScans(Number(compareScanId), Number(id));
      setComparisonResult(res);
    } catch (err) {
      console.error('Comparison failed:', err);
    } finally {
      setComparing(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGeneratingReport(true);
      await reportService.generateReport(id);
      setReportUrl(reportService.getViewReportUrl(id));
      setReportModalOpen(true);
    } catch (err) {
      console.error('Report generation error:', err);
      alert('Failed to generate report');
    } finally {
      setGeneratingReport(false);
    }
  };

  if (loading) {
    return <Loader text="Loading assessment data..." />;
  }

  if (!scan) {
    return (
      <EmptyState
        icon={Activity}
        title="Scan Not Found"
        description="The requested scan ID does not exist."
        action={<Link to="/scans">Back to Scans</Link>}
      />
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'hosts', label: `Hosts (${hosts.length})`, icon: Server },
    { id: 'ports', label: `Ports & Services (${ports.length})`, icon: Network },
    { id: 'dns', label: `DNS Intelligence (${dnsRecords.length})`, icon: Globe },
    { id: 'recon', label: `Passive Recon (${reconData.length})`, icon: Compass },
    { id: 'findings', label: `Findings (${findings.length})`, icon: AlertTriangle },
    { id: 'compare', label: 'Compare', icon: GitCompare },
  ];

  return (
    <div className={styles.container}>
      {/* Header Area */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <Link to="/scans" className={styles.backBtn} title="Back to Scans">
            <ArrowLeft size={16} />
          </Link>
          <div className={styles.titleArea}>
            <div className={styles.scanTitle}>
              Scan #{scan.id}
              <StatusBadge status={scan.status} />
              {isPolling && (
                <span style={{ fontSize: '11px', color: 'var(--cyan-primary)', fontWeight: 500 }}>
                  (Live Polling...)
                </span>
              )}
            </div>
            <div className={styles.scanMeta}>
              <span>
                Target: <Link to={`/targets/${scan.target_id}`}>{scan.target?.name || `Target #${scan.target_id}`}</Link>
              </span>
              <span>•</span>
              <code>{scan.target?.target}</code>
              <span>•</span>
              <span>Profile: <strong>{scan.profile}</strong></span>
            </div>
          </div>
        </div>

        <div className={styles.headerActions}>
          <button onClick={loadScanData} className={styles.backBtn} title="Refresh Data">
            <RefreshCw size={14} />
          </button>

          {(scan.status === 'running' || scan.status === 'queued') && (
            <button
              onClick={handleCancelScan}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(244, 63, 94, 0.15)',
                color: '#fb7185',
                border: '1px solid rgba(244, 63, 94, 0.3)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Ban size={14} />
              Cancel Scan
            </button>
          )}

          {scan.raw_output_available && (
            <a
              href={scanService.getRawXmlUrl(scan.id)}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(255, 255, 255, 0.06)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                fontSize: '13px',
                fontWeight: 500,
              }}
            >
              <Download size={14} />
              Raw Nmap XML
            </a>
          )}

          {scan.status === 'completed' && (
            <button
              onClick={handleGenerateReport}
              disabled={generatingReport}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                background: 'linear-gradient(135deg, var(--cyan-primary), #0284c7)',
                color: 'white',
                border: 'none',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <FileText size={14} />
              {generatingReport ? 'Generating...' : 'Assessment Report'}
            </button>
          )}
        </div>
      </div>

      {/* Tabs Navigation */}
      <nav className={styles.tabsNav}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`${styles.tabBtn} ${isActive ? styles.tabBtnActive : ''}`}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className={styles.tabContent}>
          {scan.error_message && (
            <div
              style={{
                background: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.4)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                color: '#fb7185',
                fontSize: '13px',
              }}
            >
              <strong>Execution Notice:</strong> {scan.error_message}
            </div>
          )}

          {/* Quick Metrics */}
          <div className={styles.grid3}>
            <div className={styles.statBox}>
              <div className={styles.statBoxLabel}>Execution Duration</div>
              <div className={styles.statBoxValue}>
                {scan.duration != null ? `${scan.duration}s` : scan.status === 'running' ? 'Scanning...' : '-'}
              </div>
            </div>

            <div className={styles.statBox}>
              <div className={styles.statBoxLabel}>Discovered Hosts</div>
              <div className={styles.statBoxValue}>{hosts.length}</div>
            </div>

            <div className={styles.statBox}>
              <div className={styles.statBoxLabel}>Open Ports Detected</div>
              <div className={styles.statBoxValue}>
                {ports.filter((p) => p.state === 'open').length}
              </div>
            </div>

            <div className={styles.statBox}>
              <div className={styles.statBoxLabel}>Security Policy Findings</div>
              <div className={styles.statBoxValue}>{findings.length}</div>
            </div>
          </div>

          {/* Module Outcomes Table */}
          <div className={styles.card}>
            <h3 className={styles.cardTitle}>
              <Layers size={18} color="var(--cyan-primary)" />
              Assessment Modules Outcome
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Individual collection modules execute independently to ensure maximum intelligence retrieval.
            </p>

            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                  <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Collection Module</th>
                  <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Outcome Status</th>
                  <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Details</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '12px 14px', fontWeight: 600 }}>Nmap Network Discovery & Services</td>
                  <td style={{ padding: '12px 14px' }}>
                    <StatusBadge status={scan.nmap_status} />
                  </td>
                  <td style={{ padding: '12px 14px', color: 'var(--text-secondary)' }}>
                    {scan.nmap_status === 'success'
                      ? `${hosts.length} host(s), ${ports.length} port(s) parsed and normalized`
                      : scan.error_message || 'Nmap scan execution incomplete or skipped'}
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '12px 14px', fontWeight: 600 }}>DNS Intelligence & DMARC</td>
                  <td style={{ padding: '12px 14px' }}>
                    <StatusBadge status={scan.dns_status} />
                  </td>
                  <td style={{ padding: '12px 14px', color: 'var(--text-secondary)' }}>
                    {scan.dns_status === 'skipped'
                      ? 'Skipped (target is a raw IP address)'
                      : `${dnsRecords.length} record(s) collected`}
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '12px 14px', fontWeight: 600 }}>Passive Reconnaissance (WHOIS)</td>
                  <td style={{ padding: '12px 14px' }}>
                    <StatusBadge status={scan.recon_status} />
                  </td>
                  <td style={{ padding: '12px 14px', color: 'var(--text-secondary)' }}>
                    {scan.recon_status === 'partial'
                      ? 'Optional WHOIS lookup degraded gracefully; core scan completed'
                      : `${reconData.length} recon key-values stored`}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: HOSTS */}
      {activeTab === 'hosts' && (
        <div className={styles.tabContent}>
          <div className={styles.card}>
            <h3 className={styles.cardTitle}>
              <Server size={18} color="var(--cyan-primary)" />
              Discovered Host Snapshots
            </h3>

            {hosts.length > 0 ? (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>IP Address</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Hostname</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Status</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>OS Fingerprint</th>
                  </tr>
                </thead>
                <tbody>
                  {hosts.map((h) => (
                    <tr key={h.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 600 }}>{h.ip}</td>
                      <td style={{ padding: '12px 14px' }}>{h.hostname || '-'}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <StatusBadge status={h.status} />
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        {h.os ? (
                          <span style={{ color: 'var(--cyan-primary)' }}>{h.os}</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>Not detected</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <EmptyState
                icon={Server}
                title="No Hosts Discovered"
                description={
                  scan.status === 'running'
                    ? 'Host discovery in progress...'
                    : 'No active hosts discovered in this scan run.'
                }
              />
            )}
          </div>
        </div>
      )}

      {/* TAB 3: PORTS & SERVICES */}
      {activeTab === 'ports' && (
        <div className={styles.tabContent}>
          <div className={styles.card}>
            <h3 className={styles.cardTitle}>
              <Network size={18} color="var(--cyan-primary)" />
              Enumerated Network Services & Ports
            </h3>

            {ports.length > 0 ? (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Port</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Protocol</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>State</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Service</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Product / Version</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Extra Info</th>
                  </tr>
                </thead>
                <tbody>
                  {ports.map((p) => (
                    <tr key={p.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {p.port_number}
                      </td>
                      <td style={{ padding: '12px 14px', textTransform: 'uppercase' }}>{p.protocol}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <span
                          style={{
                            color: p.state === 'open' ? 'var(--status-success)' : 'var(--text-muted)',
                            fontWeight: 600,
                          }}
                        >
                          {p.state}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px', color: 'var(--cyan-primary)', fontWeight: 500 }}>
                        {p.service || 'unknown'}
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        {p.product} {p.version && <span style={{ color: 'var(--text-muted)' }}>v{p.version}</span>}
                      </td>
                      <td style={{ padding: '12px 14px', color: 'var(--text-muted)', fontSize: '12px' }}>
                        {p.extra_info || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <EmptyState
                icon={Network}
                title="No Open Ports"
                description={
                  scan.status === 'running'
                    ? 'Port enumeration in progress...'
                    : 'No open ports were detected with the selected profile.'
                }
              />
            )}
          </div>
        </div>
      )}

      {/* TAB 4: DNS */}
      {activeTab === 'dns' && (
        <div className={styles.tabContent}>
          <div className={styles.card}>
            <h3 className={styles.cardTitle}>
              <Globe size={18} color="var(--cyan-primary)" />
              DNS Intelligence & Policies
            </h3>

            {dnsRecords.length > 0 ? (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Type</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Query Name</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Resolved Value</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>TTL</th>
                  </tr>
                </thead>
                <tbody>
                  {dnsRecords.map((r) => (
                    <tr key={r.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '12px 14px' }}>
                        <span
                          style={{
                            padding: '2px 8px',
                            background: 'rgba(255, 255, 255, 0.08)',
                            borderRadius: '4px',
                            fontWeight: 600,
                            fontSize: '11px',
                          }}
                        >
                          {r.record_type}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <code>{r.name}</code>
                      </td>
                      <td style={{ padding: '12px 14px', wordBreak: 'break-all' }}>{r.value}</td>
                      <td style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>{r.ttl || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <EmptyState
                icon={Globe}
                title="DNS Records Unavailable"
                description={
                  scan.target?.target_type === 'ip'
                    ? 'DNS intelligence is not applicable to raw IP targets.'
                    : 'No DNS records were collected for this target.'
                }
              />
            )}
          </div>
        </div>
      )}

      {/* TAB 5: RECON */}
      {activeTab === 'recon' && (
        <div className={styles.tabContent}>
          <div className={styles.card}>
            <h3 className={styles.cardTitle}>
              <Compass size={18} color="var(--cyan-primary)" />
              Passive Reconnaissance & WHOIS Metadata
            </h3>

            {reconData.length > 0 ? (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Category</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Key</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Value</th>
                    <th style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>Source</th>
                  </tr>
                </thead>
                <tbody>
                  {reconData.map((r) => (
                    <tr key={r.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '12px 14px', textTransform: 'capitalize' }}>
                        {r.category.replace('_', ' ')}
                      </td>
                      <td style={{ padding: '12px 14px', fontWeight: 600 }}>{r.key}</td>
                      <td style={{ padding: '12px 14px', wordBreak: 'break-all' }}>{r.value}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <code style={{ fontSize: '11px' }}>{r.source}</code>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <EmptyState
                icon={Compass}
                title="Recon Data Unavailable"
                description="No WHOIS or reverse DNS records recorded for this assessment run."
              />
            )}
          </div>
        </div>
      )}

      {/* TAB 6: FINDINGS */}
      {activeTab === 'findings' && (
        <div className={styles.tabContent}>
          {findings.length > 0 ? (
            findings.map((f) => (
              <div key={f.id} className={styles.findingCard}>
                <div className={styles.findingHeader}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <SeverityBadge severity={f.severity} />
                    <strong style={{ fontSize: '15px', color: 'var(--text-primary)' }}>
                      [{f.rule_id}] {f.title}
                    </strong>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Category: <strong>{f.category}</strong> • Source: <code>{f.source}</code>
                  </div>
                </div>

                <div className={styles.findingBody}>
                  <p style={{ marginBottom: '10px' }}>{f.description}</p>

                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
                    Observed Evidence:
                  </div>
                  <div className={styles.evidenceBox}>{f.evidence}</div>

                  <div className={styles.recommendationBox}>
                    <strong>Recommended Review:</strong> {f.recommendation}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <EmptyState
              icon={AlertTriangle}
              title="No Policy Findings Identified"
              description="No security policy non-compliance issues were identified for the accessible modules."
            />
          )}
        </div>
      )}

      {/* TAB 7: COMPARE */}
      {activeTab === 'compare' && (
        <div className={styles.tabContent}>
          <div className={styles.card}>
            <h3 className={styles.cardTitle}>
              <GitCompare size={18} color="var(--cyan-primary)" />
              Scan-to-Scan Comparative Analysis
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '18px' }}>
              Compare this current scan (#{scan.id}) against another scan of the same target to detect newly exposed ports, removed services, or resolved findings.
            </p>

            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
              <select
                className={styles.select}
                value={compareScanId}
                onChange={(e) => setCompareScanId(e.target.value)}
                style={{
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '9px 14px',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                }}
              >
                <option value="">Select Baseline Scan</option>
                {allTargetScans.map((s) => (
                  <option key={s.id} value={s.id}>
                    Scan #{s.id} ({s.profile} - {new Date(s.started_at || s.created_at).toLocaleDateString()})
                  </option>
                ))}
              </select>

              <button
                onClick={handleRunComparison}
                disabled={!compareScanId || comparing}
                style={{
                  padding: '9px 18px',
                  background: 'linear-gradient(135deg, var(--cyan-primary), #0284c7)',
                  color: 'white',
                  fontWeight: 600,
                  borderRadius: 'var(--radius-md)',
                  border: 'none',
                  fontSize: '13px',
                  cursor: compareScanId ? 'pointer' : 'not-allowed',
                  opacity: compareScanId ? 1 : 0.5,
                }}
              >
                {comparing ? 'Analyzing Delta...' : 'Compare Scans'}
              </button>
            </div>
          </div>

          {/* Comparison Results */}
          {comparisonResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className={styles.grid3}>
                <div className={styles.statBox}>
                  <div className={styles.statBoxLabel}>Added Hosts</div>
                  <div className={styles.statBoxValue} style={{ color: 'var(--status-success)' }}>
                    +{comparisonResult.added_hosts.length}
                  </div>
                </div>
                <div className={styles.statBox}>
                  <div className={styles.statBoxLabel}>Removed Hosts</div>
                  <div className={styles.statBoxValue} style={{ color: 'var(--status-failed)' }}>
                    -{comparisonResult.removed_hosts.length}
                  </div>
                </div>
                <div className={styles.statBox}>
                  <div className={styles.statBoxLabel}>Added Open Ports</div>
                  <div className={styles.statBoxValue} style={{ color: 'var(--status-success)' }}>
                    +{comparisonResult.added_ports.length}
                  </div>
                </div>
                <div className={styles.statBox}>
                  <div className={styles.statBoxLabel}>Removed Ports</div>
                  <div className={styles.statBoxValue} style={{ color: 'var(--status-failed)' }}>
                    -{comparisonResult.removed_ports.length}
                  </div>
                </div>
                <div className={styles.statBox}>
                  <div className={styles.statBoxLabel}>New Findings</div>
                  <div className={styles.statBoxValue} style={{ color: 'var(--status-failed)' }}>
                    +{comparisonResult.new_findings.length}
                  </div>
                </div>
                <div className={styles.statBox}>
                  <div className={styles.statBoxLabel}>Resolved Findings</div>
                  <div className={styles.statBoxValue} style={{ color: 'var(--status-success)' }}>
                    -{comparisonResult.resolved_findings.length}
                  </div>
                </div>
              </div>

              {/* Added Ports */}
              {comparisonResult.added_ports.length > 0 && (
                <div className={styles.card}>
                  <h4 style={{ fontSize: '15px', color: 'var(--status-success)', marginBottom: '12px' }}>
                    + Newly Discovered Ports
                  </h4>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
                        <th style={{ padding: '8px 12px' }}>IP</th>
                        <th style={{ padding: '8px 12px' }}>Port</th>
                        <th style={{ padding: '8px 12px' }}>Protocol</th>
                        <th style={{ padding: '8px 12px' }}>Service</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonResult.added_ports.map((p, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '8px 12px' }}>{p.ip}</td>
                          <td style={{ padding: '8px 12px', fontWeight: 600 }}>{p.port_number}</td>
                          <td style={{ padding: '8px 12px' }}>{p.protocol}</td>
                          <td style={{ padding: '8px 12px' }}>{p.service || 'unknown'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Removed Ports */}
              {comparisonResult.removed_ports.length > 0 && (
                <div className={styles.card}>
                  <h4 style={{ fontSize: '15px', color: 'var(--status-failed)', marginBottom: '12px' }}>
                    - Closed / Removed Ports
                  </h4>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
                        <th style={{ padding: '8px 12px' }}>IP</th>
                        <th style={{ padding: '8px 12px' }}>Port</th>
                        <th style={{ padding: '8px 12px' }}>Protocol</th>
                        <th style={{ padding: '8px 12px' }}>Service</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonResult.removed_ports.map((p, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '8px 12px' }}>{p.ip}</td>
                          <td style={{ padding: '8px 12px', fontWeight: 600 }}>{p.port_number}</td>
                          <td style={{ padding: '8px 12px' }}>{p.protocol}</td>
                          <td style={{ padding: '8px 12px' }}>{p.service || 'unknown'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Changed Services */}
              {comparisonResult.changed_services.length > 0 && (
                <div className={styles.card}>
                  <h4 style={{ fontSize: '15px', color: '#fbbf24', marginBottom: '12px' }}>
                    ~ Changed Service Versions
                  </h4>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
                        <th style={{ padding: '8px 12px' }}>Port</th>
                        <th style={{ padding: '8px 12px' }}>Baseline Version</th>
                        <th style={{ padding: '8px 12px' }}>Current Version</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonResult.changed_services.map((cs, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '8px 12px', fontWeight: 600 }}>
                            {cs.port_number}/{cs.protocol}
                          </td>
                          <td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>
                            {cs.before.service} {cs.before.version}
                          </td>
                          <td style={{ padding: '8px 12px', color: 'var(--cyan-primary)' }}>
                            {cs.after.service} {cs.after.version}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Report Modal */}
      <Modal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        title={`Assessment Report: Scan #${scan.id}`}
        maxWidth="950px"
        footer={
          <>
            <a
              href={reportService.getDownloadReportUrl(scan.id)}
              download
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(255, 255, 255, 0.08)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                fontSize: '13px',
                textDecoration: 'none',
              }}
            >
              <Download size={14} />
              Download HTML
            </a>
            <button
              onClick={() => setReportModalOpen(false)}
              style={{
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--cyan-primary)',
                color: '#000',
                border: 'none',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              Close
            </button>
          </>
        }
      >
        <div style={{ height: '70vh', width: '100%' }}>
          <iframe
            src={reportUrl}
            title="Security Assessment Report"
            style={{ width: '100%', height: '100%', border: 'none', borderRadius: 'var(--radius-md)', background: '#fff' }}
          />
        </div>
      </Modal>
    </div>
  );
}
