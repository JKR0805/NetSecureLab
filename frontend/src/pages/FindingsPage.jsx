import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  Search,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Download,
  FileText,
} from 'lucide-react';
import { findingService } from '../services/findingService';
import { SeverityBadge, FindingStatusBadge } from '../components/common/Badge';
import { Loader, EmptyState } from '../components/common/Loader';
import styles from './TargetsPage.module.css';

export function FindingsPage() {
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedId, setExpandedId] = useState(null);
  const [editingNotes, setEditingNotes] = useState({});
  const [updatingId, setUpdatingId] = useState(null);

  const fetchFindings = useCallback(async () => {
    try {
      setLoading(true);
      const params = {};
      if (selectedSeverity !== 'all') params.severity = selectedSeverity;
      if (selectedCategory !== 'all') params.category = selectedCategory;

      const data = await findingService.listAllFindings(params);
      setFindings(data);
    } catch (err) {
      console.error('Failed to load findings:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedSeverity, selectedCategory]);

  useEffect(() => {
    fetchFindings();
  }, [fetchFindings]);

  const toggleExpand = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const handleStatusChange = async (findingId, newStatus) => {
    try {
      setUpdatingId(findingId);
      const updated = await findingService.updateFinding(findingId, { status: newStatus });
      setFindings((prev) => prev.map((f) => (f.id === findingId ? { ...f, status: updated.status } : f)));
    } catch (err) {
      console.error('Failed to update finding status:', err);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleSaveNotes = async (findingId) => {
    const note = editingNotes[findingId];
    if (note === undefined) return;
    try {
      setUpdatingId(findingId);
      const updated = await findingService.updateFinding(findingId, { notes: note });
      setFindings((prev) => prev.map((f) => (f.id === findingId ? { ...f, notes: updated.notes } : f)));
    } catch (err) {
      console.error('Failed to save finding note:', err);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleExportCsv = async () => {
    const params = {};
    if (selectedSeverity !== 'all') params.severity = selectedSeverity;
    if (selectedCategory !== 'all') params.category = selectedCategory;
    await findingService.exportCsv(params);
  };

  const handleExportJson = async () => {
    const params = {};
    if (selectedSeverity !== 'all') params.severity = selectedSeverity;
    if (selectedCategory !== 'all') params.category = selectedCategory;
    await findingService.exportJson(params);
  };

  const filtered = findings.filter(
    (f) =>
      f.title.toLowerCase().includes(search.toLowerCase()) ||
      f.rule_id.toLowerCase().includes(search.toLowerCase()) ||
      f.evidence.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className={styles.container}>
      {/* Top filters bar */}
      <div className={styles.topBar}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div className={styles.searchBox}>
            <Search size={16} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search findings by rule ID, title, or evidence..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className={styles.select}
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            style={{ width: '160px', padding: '8px 12px', fontSize: '13px' }}
          >
            <option value="all">All Severities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="informational">Informational</option>
          </select>

          <select
            className={styles.select}
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{ width: '180px', padding: '8px 12px', fontSize: '13px' }}
          >
            <option value="all">All Categories</option>
            <option value="Service Exposure">Service Exposure</option>
            <option value="Fingerprinting">Fingerprinting</option>
            <option value="Web Discovery">Web Discovery</option>
            <option value="DNS Security">DNS Security</option>
            <option value="Mail Infrastructure">Mail Infrastructure</option>
            <option value="Service Info">Service Info</option>
          </select>

          <button onClick={fetchFindings} className={styles.actionBtn} style={{ padding: '8px' }} title="Refresh findings">
            <RefreshCw size={14} />
          </button>

          <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
            <button
              onClick={handleExportCsv}
              className={styles.secondaryBtn}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '8px 14px', fontSize: '13px' }}
              title="Export filtered findings as CSV"
            >
              <Download size={14} /> Export CSV
            </button>
            <button
              onClick={handleExportJson}
              className={styles.secondaryBtn}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '8px 14px', fontSize: '13px' }}
              title="Export filtered findings as JSON"
            >
              <FileText size={14} /> Export JSON
            </button>
          </div>
        </div>
      </div>

      {/* Findings Table */}
      <div className={styles.card}>
        {loading ? (
          <Loader text="Loading findings across assessments..." />
        ) : filtered.length > 0 ? (
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ width: '40px' }}></th>
                <th>Rule ID</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Title</th>
                <th>Category</th>
                <th>Scan</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((f) => {
                const isExpanded = expandedId === f.id;
                return (
                  <React.Fragment key={f.id}>
                    <tr
                      onClick={() => toggleExpand(f.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td>
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </td>
                      <td>
                        <strong style={{ color: 'var(--cyan-primary)' }}>{f.rule_id}</strong>
                      </td>
                      <td>
                        <SeverityBadge severity={f.severity} />
                      </td>
                      <td>
                        <FindingStatusBadge status={f.status} />
                      </td>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {f.title}
                      </td>
                      <td>{f.category}</td>
                      <td>
                        <Link
                          to={`/scans/${f.scan_id}?tab=findings`}
                          onClick={(e) => e.stopPropagation()}
                          className={styles.link}
                        >
                          #{f.scan_id}
                        </Link>
                      </td>
                      <td>
                        <code style={{ fontSize: '11px' }}>{f.source}</code>
                      </td>
                    </tr>

                    {isExpanded && (
                      <tr style={{ background: 'rgba(8, 12, 20, 0.6)' }}>
                        <td colSpan={8} style={{ padding: '20px 24px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255, 255, 255, 0.03)', padding: '10px 14px', borderRadius: 'var(--radius-sm)' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <strong style={{ color: 'var(--text-primary)', fontSize: '13px' }}>Status Workflow:</strong>
                                <select
                                  value={f.status || 'open'}
                                  onChange={(e) => handleStatusChange(f.id, e.target.value)}
                                  disabled={updatingId === f.id}
                                  className={styles.select}
                                  style={{ padding: '4px 10px', fontSize: '12px', width: '150px' }}
                                >
                                  <option value="open">Open</option>
                                  <option value="acknowledged">Acknowledged</option>
                                  <option value="accepted_risk">Accepted Risk</option>
                                  <option value="remediated">Remediated</option>
                                </select>
                              </div>
                              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                Detected: {new Date(f.created_at).toLocaleString()}
                              </span>
                            </div>

                            <div>
                              <strong style={{ color: 'var(--text-primary)' }}>Description: </strong>
                              <span>{f.description}</span>
                            </div>

                            <div>
                              <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '4px' }}>
                                Observed Technical Evidence:
                              </strong>
                              <div
                                style={{
                                  background: '#090d16',
                                  border: '1px solid rgba(6, 182, 212, 0.2)',
                                  color: '#38bdf8',
                                  padding: '10px 14px',
                                  borderRadius: 'var(--radius-sm)',
                                  fontFamily: 'monospace',
                                  fontSize: '12px',
                                  whiteSpace: 'pre-wrap',
                                }}
                              >
                                {f.evidence}
                              </div>
                            </div>

                            <div
                              style={{
                                background: 'rgba(59, 130, 246, 0.08)',
                                borderLeft: '3px solid #3b82f6',
                                padding: '10px 14px',
                                borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                                fontSize: '13px',
                                color: '#93c5fd',
                              }}
                            >
                              <strong>Remediation / Administrator Recommendation: </strong>
                              {f.recommendation}
                            </div>

                            {/* Remediation Notes */}
                            <div style={{ background: 'rgba(15, 23, 42, 0.4)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '12px 14px' }}>
                              <strong style={{ display: 'block', color: 'var(--text-primary)', fontSize: '13px', marginBottom: '6px' }}>
                                Remediation & Audit Notes
                              </strong>
                              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                <input
                                  type="text"
                                  placeholder="Add notes (e.g. ticket JIRA-1234 assigned, firewall rule applied)..."
                                  value={editingNotes[f.id] !== undefined ? editingNotes[f.id] : (f.notes || '')}
                                  onChange={(e) => setEditingNotes({ ...editingNotes, [f.id]: e.target.value })}
                                  className={styles.input}
                                  style={{ flex: 1, padding: '6px 12px', fontSize: '13px' }}
                                />
                                <button
                                  onClick={() => handleSaveNotes(f.id)}
                                  disabled={updatingId === f.id}
                                  className={styles.primaryBtn}
                                  style={{ padding: '6px 14px', fontSize: '12px' }}
                                >
                                  {updatingId === f.id ? 'Saving...' : 'Save Note'}
                                </button>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        ) : (
          <EmptyState
            icon={AlertTriangle}
            title="No Findings Match Filter"
            description="Adjust severity, category, or search keywords to view security policy observations."
          />
        )}
      </div>
    </div>
  );
}
