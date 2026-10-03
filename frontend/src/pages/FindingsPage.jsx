import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  Search,
  Filter,
  RefreshCw,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Info,
} from 'lucide-react';
import { findingService } from '../services/findingService';
import { SeverityBadge } from '../components/common/Badge';
import { Loader, EmptyState } from '../components/common/Loader';
import styles from './TargetsPage.module.css';

export function FindingsPage() {
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedId, setExpandedId] = useState(null);

  const fetchFindings = async () => {
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
  };

  useEffect(() => {
    fetchFindings();
  }, [selectedSeverity, selectedCategory]);

  const toggleExpand = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
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

          <button onClick={fetchFindings} className={styles.actionBtn} style={{ padding: '8px' }}>
            <RefreshCw size={14} />
          </button>
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
                        <td colSpan={7} style={{ padding: '20px 24px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
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
