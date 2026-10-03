import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Activity,
  Play,
  Download,
  Filter,
  RefreshCw,
  Search,
  ExternalLink,
  Ban,
} from 'lucide-react';
import { scanService } from '../services/scanService';
import { targetService } from '../services/targetService';
import { StatusBadge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Loader, EmptyState } from '../components/common/Loader';
import styles from './TargetsPage.module.css';

export function ScansPage() {
  const [scans, setScans] = useState([]);
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [selectedTargetId, setSelectedTargetId] = useState('');
  const [scanProfile, setScanProfile] = useState('standard');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const navigate = useNavigate();

  const fetchScans = async () => {
    try {
      setLoading(true);
      const data = await scanService.listScans();
      setScans(data);
    } catch (err) {
      console.error('Failed to load scans:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTargets = async () => {
    try {
      const data = await targetService.listTargets();
      const authorizedTargets = data.filter((t) => t.authorization_confirmed);
      setTargets(authorizedTargets);
      if (authorizedTargets.length > 0 && !selectedTargetId) {
        setSelectedTargetId(authorizedTargets[0].id);
      }
    } catch (err) {
      console.error('Failed to load targets:', err);
    }
  };

  useEffect(() => {
    fetchScans();
    fetchTargets();

    // Auto-refresh scan list every 5 seconds if any scan is queued or running
    const interval = setInterval(() => {
      setScans((prev) => {
        const hasActive = prev.some((s) => s.status === 'queued' || s.status === 'running');
        if (hasActive) {
          scanService.listScans().then(setScans).catch(() => {});
        }
        return prev;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleStartScan = async () => {
    if (!selectedTargetId) return;
    try {
      setSubmitting(true);
      setErrorMsg('');
      const scan = await scanService.createScan(Number(selectedTargetId), scanProfile);
      setIsScanOpen(false);
      navigate(`/scans/${scan.id}`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to start scan';
      setErrorMsg(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async (scanId) => {
    try {
      await scanService.cancelScan(scanId);
      fetchScans();
    } catch (err) {
      console.error('Failed to cancel scan:', err);
    }
  };

  const filteredScans = scans.filter((s) => {
    if (filterStatus === 'all') return true;
    return s.status === filterStatus;
  });

  return (
    <div className={styles.container}>
      {/* Top action bar */}
      <div className={styles.topBar}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select
            className={styles.select}
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            style={{ width: '180px', padding: '8px 12px', fontSize: '13px' }}
          >
            <option value="all">All Scan States</option>
            <option value="running">Running</option>
            <option value="queued">Queued</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>

          <button
            onClick={fetchScans}
            className={styles.actionBtn}
            title="Refresh Scan List"
            style={{ padding: '8px' }}
          >
            <RefreshCw size={15} />
          </button>
        </div>

        <button
          onClick={() => {
            setErrorMsg('');
            setIsScanOpen(true);
          }}
          className={styles.actionBtn}
          style={{
            background: 'linear-gradient(135deg, var(--cyan-primary), #0284c7)',
            color: 'white',
            fontWeight: 600,
            padding: '8px 16px',
            border: 'none',
          }}
        >
          <Play size={15} />
          New Assessment
        </button>
      </div>

      {errorMsg && <div className={styles.errorBanner}>{errorMsg}</div>}

      {/* Scans table */}
      <div className={styles.card}>
        {loading ? (
          <Loader text="Loading assessment scans..." />
        ) : filteredScans.length > 0 ? (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Target</th>
                <th>Profile</th>
                <th>Status</th>
                <th>Modules</th>
                <th>Findings</th>
                <th>Duration</th>
                <th>Started</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredScans.map((s) => (
                <tr key={s.id}>
                  <td>
                    <strong>#{s.id}</strong>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {s.target ? s.target.name : `Target #${s.target_id}`}
                    </div>
                    {s.target && (
                      <code style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {s.target.target}
                      </code>
                    )}
                  </td>
                  <td>
                    <code style={{ fontSize: '12px' }}>{s.profile}</code>
                  </td>
                  <td>
                    <StatusBadge status={s.status} />
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      <span title={`Nmap: ${s.nmap_status}`}>
                        <StatusBadge status={s.nmap_status} />
                      </span>
                      <span title={`DNS: ${s.dns_status}`}>
                        <StatusBadge status={s.dns_status} />
                      </span>
                      <span title={`Recon: ${s.recon_status}`}>
                        <StatusBadge status={s.recon_status} />
                      </span>
                    </div>
                  </td>
                  <td>
                    <strong>{s.findings_count}</strong>
                  </td>
                  <td>{s.duration != null ? `${s.duration}s` : '-'}</td>
                  <td>{s.started_at ? new Date(s.started_at).toLocaleTimeString() : '-'}</td>
                  <td>
                    <div className={styles.actions}>
                      <Link to={`/scans/${s.id}`} className={styles.actionBtn}>
                        Inspect →
                      </Link>

                      {(s.status === 'running' || s.status === 'queued') && (
                        <button
                          onClick={() => handleCancel(s.id)}
                          className={`${styles.actionBtn} ${styles.actionBtnDelete}`}
                          title="Cancel Scan"
                        >
                          <Ban size={13} />
                        </button>
                      )}

                      {s.raw_output_available && (
                        <a
                          href={scanService.getRawXmlUrl(s.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={styles.actionBtn}
                          title="Download Raw Nmap XML"
                        >
                          <Download size={13} />
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState
            icon={Activity}
            title="No Scans Found"
            description="Start an assessment scan on an authorized target."
            action={
              <button
                onClick={() => setIsScanOpen(true)}
                className={styles.actionBtn}
                style={{
                  background: 'var(--cyan-primary)',
                  color: '#000',
                  fontWeight: 600,
                  marginTop: '12px',
                }}
              >
                Launch Scan
              </button>
            }
          />
        )}
      </div>

      {/* New Scan Modal */}
      <Modal
        isOpen={isScanOpen}
        onClose={() => setIsScanOpen(false)}
        title="Execute Security Assessment"
        footer={
          <>
            <button className={styles.actionBtn} onClick={() => setIsScanOpen(false)}>
              Cancel
            </button>
            <button
              className={styles.actionBtn}
              onClick={handleStartScan}
              disabled={submitting || targets.length === 0}
              style={{
                background: 'linear-gradient(135deg, var(--cyan-primary), #0284c7)',
                color: 'white',
                fontWeight: 600,
                border: 'none',
              }}
            >
              {submitting ? 'Starting...' : 'Execute Scan'}
            </button>
          </>
        }
      >
        {targets.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '16px' }}>
            <p style={{ color: 'var(--text-muted)', marginBottom: '14px' }}>
              No authorized targets found. You must configure and confirm authorization on a target first.
            </p>
            <Link
              to="/targets"
              className={styles.actionBtn}
              style={{ background: 'var(--cyan-primary)', color: '#000', fontWeight: 600 }}
            >
              Go to Targets
            </Link>
          </div>
        ) : (
          <>
            <div className={styles.formGroup}>
              <label>Select Authorized Target *</label>
              <select
                className={styles.select}
                value={selectedTargetId}
                onChange={(e) => setSelectedTargetId(e.target.value)}
              >
                {targets.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.target} - {t.target_type})
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.formGroup}>
              <label>Assessment Profile</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '6px' }}>
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '12px',
                    borderRadius: 'var(--radius-md)',
                    background:
                      scanProfile === 'quick' ? 'rgba(6, 182, 212, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                    border:
                      scanProfile === 'quick' ? '1px solid var(--cyan-primary)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="radio"
                    name="profile"
                    value="quick"
                    checked={scanProfile === 'quick'}
                    onChange={() => setScanProfile('quick')}
                  />
                  <div>
                    <strong style={{ color: 'var(--text-primary)' }}>Quick Discovery</strong>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      Fast host discovery only (-sn). Ping sweep without probing ports.
                    </p>
                  </div>
                </label>

                <label
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '12px',
                    borderRadius: 'var(--radius-md)',
                    background:
                      scanProfile === 'standard' ? 'rgba(6, 182, 212, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                    border:
                      scanProfile === 'standard' ? '1px solid var(--cyan-primary)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="radio"
                    name="profile"
                    value="standard"
                    checked={scanProfile === 'standard'}
                    onChange={() => setScanProfile('standard')}
                  />
                  <div>
                    <strong style={{ color: 'var(--text-primary)' }}>Standard Assessment (Recommended)</strong>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      TCP port scan of top 1,000 ports with service version detection (-sV -T4).
                    </p>
                  </div>
                </label>

                <label
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '12px',
                    borderRadius: 'var(--radius-md)',
                    background:
                      scanProfile === 'full' ? 'rgba(6, 182, 212, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                    border:
                      scanProfile === 'full' ? '1px solid var(--cyan-primary)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="radio"
                    name="profile"
                    value="full"
                    checked={scanProfile === 'full'}
                    onChange={() => setScanProfile('full')}
                  />
                  <div>
                    <strong style={{ color: 'var(--text-primary)' }}>Full Depth Assessment</strong>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      All 65,535 TCP ports with service detection, default NSE scripts, and non-fatal OS detection pass.
                    </p>
                  </div>
                </label>
              </div>
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}
