import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Crosshair,
  ShieldCheck,
  ShieldAlert,
  Play,
  ArrowLeft,
  Activity,
  GitCompare,
  Calendar,
  Layers,
} from 'lucide-react';
import { targetService } from '../services/targetService';
import { scanService } from '../services/scanService';
import { StatusBadge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Loader, EmptyState } from '../components/common/Loader';
import styles from './TargetsPage.module.css';

export function TargetDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [target, setTarget] = useState(null);
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  // Scan modal
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [scanProfile, setScanProfile] = useState('standard');
  const [scanSubmitting, setScanSubmitting] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const tData = await targetService.getTarget(id);
        setTarget(tData);
        const sData = await scanService.listScans(id);
        setScans(sData);
      } catch (err) {
        setErrorMsg('Failed to load target details');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  const handleStartScan = async () => {
    try {
      setScanSubmitting(true);
      const newScan = await scanService.createScan(target.id, scanProfile);
      setIsScanOpen(false);
      navigate(`/scans/${newScan.id}`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to start scan';
      setErrorMsg(msg);
    } finally {
      setScanSubmitting(false);
    }
  };

  if (loading) {
    return <Loader text="Loading target profile..." />;
  }

  if (!target) {
    return (
      <EmptyState
        icon={Crosshair}
        title="Target Not Found"
        description="The requested target ID does not exist in the database."
        action={
          <Link to="/targets" className={styles.actionBtn}>
            Return to Targets
          </Link>
        }
      />
    );
  }

  const completedScans = scans.filter((s) => s.status === 'completed');

  return (
    <div className={styles.container}>
      {/* Header breadcrumb & actions */}
      <div className={styles.topBar}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Link to="/targets" className={styles.actionBtn} style={{ padding: '6px' }}>
            <ArrowLeft size={16} />
          </Link>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
              {target.name}
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              <code>{target.target}</code>
              <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>•</span>
              <span style={{ textTransform: 'capitalize', color: 'var(--text-muted)', fontSize: '12px' }}>
                {target.target_type.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {completedScans.length >= 2 && (
            <Link
              to={`/scans/${completedScans[0].id}?tab=compare&with=${completedScans[1].id}`}
              className={styles.actionBtn}
              style={{ background: 'rgba(255, 255, 255, 0.06)' }}
            >
              <GitCompare size={14} />
              Compare Recent Scans
            </Link>
          )}

          <button
            onClick={() => setIsScanOpen(true)}
            disabled={!target.authorization_confirmed}
            className={styles.actionBtn}
            style={{
              background: 'linear-gradient(135deg, var(--cyan-primary), #0284c7)',
              color: 'white',
              fontWeight: 600,
              border: 'none',
              opacity: target.authorization_confirmed ? 1 : 0.5,
              cursor: target.authorization_confirmed ? 'pointer' : 'not-allowed',
            }}
          >
            <Play size={14} />
            New Assessment Scan
          </button>
        </div>
      </div>

      {errorMsg && <div className={styles.errorBanner}>{errorMsg}</div>}

      {/* Target Info Card */}
      <div
        className={styles.card}
        style={{
          padding: '24px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '20px',
        }}
      >
        <div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Authorization Status
          </span>
          <div style={{ marginTop: '6px' }}>
            {target.authorization_confirmed ? (
              <span className={`${styles.authBadge} ${styles.authConfirmed}`}>
                <ShieldCheck size={13} /> Confirmed Authorized
              </span>
            ) : (
              <span className={`${styles.authBadge} ${styles.authMissing}`}>
                <ShieldAlert size={13} /> Unauthorized
              </span>
            )}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Registered Date
          </span>
          <div style={{ marginTop: '6px', color: 'var(--text-primary)', fontWeight: 500 }}>
            {new Date(target.created_at).toLocaleString()}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Total Assessments
          </span>
          <div style={{ marginTop: '6px', color: 'var(--text-primary)', fontWeight: 700, fontSize: '18px' }}>
            {scans.length}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Description
          </span>
          <div style={{ marginTop: '6px', color: 'var(--text-secondary)', fontSize: '13px' }}>
            {target.description || 'No description provided'}
          </div>
        </div>
      </div>

      {/* Scan History for this target */}
      <div>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px', color: 'var(--text-primary)' }}>
          Assessment History
        </h3>

        <div className={styles.card}>
          {scans.length > 0 ? (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Scan ID</th>
                  <th>Profile</th>
                  <th>Status</th>
                  <th>Nmap</th>
                  <th>DNS</th>
                  <th>Recon</th>
                  <th>Findings</th>
                  <th>Duration</th>
                  <th>Started</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {scans.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <strong>#{s.id}</strong>
                    </td>
                    <td>
                      <code>{s.profile}</code>
                    </td>
                    <td>
                      <StatusBadge status={s.status} />
                    </td>
                    <td>
                      <StatusBadge status={s.nmap_status} />
                    </td>
                    <td>
                      <StatusBadge status={s.dns_status} />
                    </td>
                    <td>
                      <StatusBadge status={s.recon_status} />
                    </td>
                    <td>
                      <strong>{s.findings_count}</strong>
                    </td>
                    <td>{s.duration != null ? `${s.duration}s` : '-'}</td>
                    <td>{s.started_at ? new Date(s.started_at).toLocaleTimeString() : '-'}</td>
                    <td>
                      <Link to={`/scans/${s.id}`} className={styles.actionBtn}>
                        Inspect →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState
              icon={Activity}
              title="No Scans Executed for this Target"
              description="Execute a security scan to gather port, service, and DNS reconnaissance."
              action={
                <button
                  onClick={() => setIsScanOpen(true)}
                  disabled={!target.authorization_confirmed}
                  className={styles.actionBtn}
                  style={{
                    background: 'var(--cyan-primary)',
                    color: '#000',
                    fontWeight: 600,
                    marginTop: '12px',
                  }}
                >
                  Start First Scan
                </button>
              }
            />
          )}
        </div>
      </div>

      {/* Launch Scan Modal */}
      <Modal
        isOpen={isScanOpen}
        onClose={() => setIsScanOpen(false)}
        title={`New Assessment: ${target.name}`}
        footer={
          <>
            <button className={styles.actionBtn} onClick={() => setIsScanOpen(false)}>
              Cancel
            </button>
            <button
              className={styles.actionBtn}
              onClick={handleStartScan}
              disabled={scanSubmitting}
              style={{
                background: 'linear-gradient(135deg, var(--cyan-primary), #0284c7)',
                color: 'white',
                fontWeight: 600,
                border: 'none',
              }}
            >
              {scanSubmitting ? 'Starting...' : 'Execute Scan'}
            </button>
          </>
        }
      >
        <div style={{ marginBottom: '18px' }}>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
            Target: <code>{target.target}</code> ({target.target_type})
          </p>
        </div>

        <div className={styles.formGroup}>
          <label>Select Profile</label>
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
                  Host discovery only (-sn). Fast network ping sweep.
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
      </Modal>
    </div>
  );
}
