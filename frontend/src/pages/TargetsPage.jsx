import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Crosshair,
  Plus,
  Play,
  Trash2,
  Search,
  ShieldCheck,
  ShieldAlert,
  ExternalLink,
  Info,
} from 'lucide-react';
import { targetService } from '../services/targetService';
import { scanService } from '../services/scanService';
import { Modal } from '../components/common/Modal';
import { Loader, EmptyState } from '../components/common/Loader';
import styles from './TargetsPage.module.css';

export function TargetsPage() {
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  
  // Add Target Modal
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [addForm, setAddForm] = useState({
    name: '',
    target: '',
    target_type: 'ip',
    description: '',
    authorization_confirmed: false,
  });
  const [formSubmitting, setFormSubmitting] = useState(false);

  // New Scan Modal
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [scanProfile, setScanProfile] = useState('standard');
  const [scanSubmitting, setScanSubmitting] = useState(false);

  const navigate = useNavigate();

  const fetchTargets = useCallback(async () => {
    try {
      setLoading(true);
      const data = await targetService.listTargets();
      setTargets(data);
    } catch {
      setErrorMsg('Failed to load targets from backend');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTargets();
  }, [fetchTargets]);

  const handleCreateTarget = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!addForm.authorization_confirmed) {
      setErrorMsg('You must explicitly confirm technical authorization to add this target.');
      return;
    }

    try {
      setFormSubmitting(true);
      await targetService.createTarget(addForm);
      setIsAddOpen(false);
      setAddForm({
        name: '',
        target: '',
        target_type: 'ip',
        description: '',
        authorization_confirmed: false,
      });
      fetchTargets();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to create target. Check input format.';
      setErrorMsg(msg);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleDeleteTarget = async (targetId) => {
    if (!window.confirm('Are you sure you want to delete this target?')) return;
    setErrorMsg('');
    try {
      await targetService.deleteTarget(targetId);
      fetchTargets();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to delete target';
      setErrorMsg(msg);
    }
  };

  const handleStartScan = async () => {
    if (!selectedTarget) return;
    try {
      setScanSubmitting(true);
      const newScan = await scanService.createScan(selectedTarget.id, scanProfile);
      setIsScanOpen(false);
      navigate(`/scans/${newScan.id}`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to initiate scan';
      setErrorMsg(msg);
    } finally {
      setScanSubmitting(false);
    }
  };

  const filteredTargets = targets.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.target.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className={styles.container}>
      {/* Top Bar */}
      <div className={styles.topBar}>
        <div className={styles.searchBox}>
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search targets by name or host..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <button
          onClick={() => {
            setErrorMsg('');
            setIsAddOpen(true);
          }}
          className={styles.actionBtn}
          style={{
            background: 'linear-gradient(135deg, var(--cyan-primary), #0284c7)',
            color: 'white',
            fontWeight: 600,
            padding: '8px 16px',
            borderColor: 'transparent',
          }}
        >
          <Plus size={16} />
          <span>Add Target</span>
        </button>
      </div>

      {errorMsg && <div className={styles.errorBanner}>{errorMsg}</div>}

      {/* Target Table */}
      <div className={styles.card}>
        {loading ? (
          <Loader text="Loading authorized targets..." />
        ) : filteredTargets.length > 0 ? (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Target Name</th>
                <th>Target String</th>
                <th>Type</th>
                <th>Authorization</th>
                <th>Scans</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTargets.map((t) => (
                <tr key={t.id}>
                  <td>
                    <div className={styles.targetName}>
                      <Link to={`/targets/${t.id}`} style={{ color: 'var(--text-primary)' }}>
                        {t.name}
                      </Link>
                      {t.description && <span className={styles.targetDesc}>{t.description}</span>}
                    </div>
                  </td>
                  <td>
                    <code>{t.target}</code>
                  </td>
                  <td>
                    <span style={{ textTransform: 'capitalize', fontSize: '12px' }}>
                      {t.target_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td>
                    {t.authorization_confirmed ? (
                      <span className={`${styles.authBadge} ${styles.authConfirmed}`}>
                        <ShieldCheck size={12} />
                        Authorized
                      </span>
                    ) : (
                      <span className={`${styles.authBadge} ${styles.authMissing}`}>
                        <ShieldAlert size={12} />
                        Unauthorized
                      </span>
                    )}
                  </td>
                  <td>
                    <strong>{t.scan_count}</strong>
                  </td>
                  <td>{new Date(t.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className={styles.actions}>
                      <button
                        className={styles.actionBtn}
                        title="Start Assessment Scan"
                        disabled={!t.authorization_confirmed}
                        onClick={() => {
                          setSelectedTarget(t);
                          setIsScanOpen(true);
                        }}
                        style={!t.authorization_confirmed ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
                      >
                        <Play size={13} color="var(--cyan-primary)" />
                        Scan
                      </button>

                      <Link to={`/targets/${t.id}`} className={styles.actionBtn} title="View Details">
                        <ExternalLink size={13} />
                      </Link>

                      <button
                        className={`${styles.actionBtn} ${styles.actionBtnDelete}`}
                        title={
                          t.scan_count > 0
                            ? 'Cannot delete target with existing scans'
                            : 'Delete Target'
                        }
                        disabled={t.scan_count > 0}
                        onClick={() => handleDeleteTarget(t.id)}
                        style={t.scan_count > 0 ? { opacity: 0.35, cursor: 'not-allowed' } : {}}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState
            icon={Crosshair}
            title="No Targets Configured"
            description="Add an authorized network address, domain, or application endpoint to initiate assessments."
            action={
              <button
                onClick={() => setIsAddOpen(true)}
                className={styles.actionBtn}
                style={{
                  background: 'var(--cyan-primary)',
                  color: '#000',
                  fontWeight: 600,
                  marginTop: '12px',
                }}
              >
                Add Your First Target
              </button>
            }
          />
        )}
      </div>

      {/* Add Target Modal */}
      <Modal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        title="Add Assessment Target"
        footer={
          <>
            <button className={styles.actionBtn} onClick={() => setIsAddOpen(false)}>
              Cancel
            </button>
            <button
              className={styles.actionBtn}
              onClick={handleCreateTarget}
              disabled={formSubmitting}
              style={{
                background: 'var(--cyan-primary)',
                color: '#000',
                fontWeight: 600,
                border: 'none',
              }}
            >
              {formSubmitting ? 'Saving...' : 'Register Target'}
            </button>
          </>
        }
      >
        <form onSubmit={handleCreateTarget}>
          <div className={styles.formGroup}>
            <label>Target Name *</label>
            <input
              type="text"
              className={styles.input}
              placeholder="e.g. Lab Web Gateway"
              value={addForm.name}
              onChange={(e) => setAddForm({ ...addForm, name: e.target.value })}
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label>Target Type *</label>
            <select
              className={styles.select}
              value={addForm.target_type}
              onChange={(e) => setAddForm({ ...addForm, target_type: e.target.value })}
            >
              <option value="ip">IP Address (e.g. 192.168.1.50)</option>
              <option value="domain">Domain Name (e.g. scanme.nmap.org)</option>
              <option value="hostname">Hostname (e.g. lab-srv.local)</option>
              <option value="web_application">Web Application URL (e.g. https://example.com)</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label>Target Value *</label>
            <input
              type="text"
              className={styles.input}
              placeholder={
                addForm.target_type === 'ip'
                  ? '192.168.1.1'
                  : addForm.target_type === 'domain'
                  ? 'scanme.nmap.org'
                  : addForm.target_type === 'web_application'
                  ? 'https://app.local:8080'
                  : 'gateway.local'
              }
              value={addForm.target}
              onChange={(e) => setAddForm({ ...addForm, target: e.target.value })}
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label>Description (Optional)</label>
            <textarea
              className={styles.textarea}
              placeholder="Context or notes about the target environment..."
              value={addForm.description}
              onChange={(e) => setAddForm({ ...addForm, description: e.target.value })}
            />
          </div>

          {/* Legal / Technical Authorization Control */}
          <div className={styles.authCallout}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, marginBottom: '4px' }}>
              <Info size={16} /> Technical Authorization Policy
            </div>
            NetSecureLab enforces technical access controls. Scans cannot be executed against targets without explicit confirmation of authorization.
          </div>

          <label className={styles.checkboxContainer}>
            <input
              type="checkbox"
              checked={addForm.authorization_confirmed}
              onChange={(e) =>
                setAddForm({ ...addForm, authorization_confirmed: e.target.checked })
              }
            />
            <span className={styles.checkboxLabel}>
              I confirm I have explicit legal authorization to perform security reconnaissance and scanning on this target.
            </span>
          </label>
        </form>
      </Modal>

      {/* Start Scan Modal */}
      <Modal
        isOpen={isScanOpen}
        onClose={() => setIsScanOpen(false)}
        title={`New Assessment: ${selectedTarget?.name}`}
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
            Target: <code>{selectedTarget?.target}</code> ({selectedTarget?.target_type})
          </p>
        </div>

        <div className={styles.formGroup}>
          <label>Scan Profile</label>
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
                  Host discovery only (-sn). Fast network ping sweep without probing ports.
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
