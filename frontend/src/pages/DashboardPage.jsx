import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Crosshair,
  Server,
  Network,
  Cpu,
  AlertTriangle,
  Activity,
} from 'lucide-react';
import { dashboardService } from '../services/dashboardService';
import { StatusBadge } from '../components/common/Badge';
import { Loader, EmptyState } from '../components/common/Loader';
import styles from './DashboardPage.module.css';

export function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await dashboardService.getStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  if (loading) {
    return <Loader text="Loading security intelligence metrics..." />;
  }

  const metrics = [
    { label: 'Targets in Scope', value: stats?.total_targets ?? 0, icon: Crosshair },
    { label: 'Discovered Hosts', value: stats?.total_hosts ?? 0, icon: Server },
    { label: 'Open Ports', value: stats?.total_open_ports ?? 0, icon: Network },
    { label: 'Identified Services', value: stats?.total_services ?? 0, icon: Cpu },
    { label: 'Security Findings', value: stats?.total_findings ?? 0, icon: AlertTriangle },
  ];

  const severityData = stats?.findings_by_severity || {
    high: 0,
    medium: 0,
    low: 0,
    informational: 0,
  };

  const totalFindings =
    severityData.high + severityData.medium + severityData.low + severityData.informational;

  const severityBars = [
    { label: 'High Severity', count: severityData.high, color: 'var(--sev-high-text)' },
    { label: 'Medium Severity', count: severityData.medium, color: 'var(--sev-med-text)' },
    { label: 'Low Severity', count: severityData.low, color: 'var(--sev-low-text)' },
    { label: 'Informational', count: severityData.informational, color: 'var(--sev-info-text)' },
  ];

  return (
    <div className={styles.container}>
      {/* Metrics Row */}
      <div className={styles.metricsGrid}>
        {metrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <div key={idx} className={styles.metricCard}>
              <div className={styles.metricHeader}>
                <span className={styles.metricLabel}>{m.label}</span>
                <div className={styles.metricIcon}>
                  <Icon size={18} />
                </div>
              </div>
              <div className={styles.metricValue}>{m.value}</div>
            </div>
          );
        })}
      </div>

      {/* Row 2: Severity Distribution & Recent Scans */}
      <div className={styles.chartsRow}>
        {/* Severity Distribution */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Findings by Severity</h2>
            <Link to="/findings" className={styles.link} style={{ fontSize: '13px' }}>
              View all
            </Link>
          </div>

          <div className={styles.severityList}>
            {severityBars.map((sev) => {
              const pct = totalFindings > 0 ? Math.round((sev.count / totalFindings) * 100) : 0;
              return (
                <div key={sev.label} className={styles.severityItem}>
                  <div className={styles.severityHeader}>
                    <span style={{ color: sev.color }}>{sev.label}</span>
                    <span style={{ color: 'var(--text-muted)' }}>
                      {sev.count} ({pct}%)
                    </span>
                  </div>
                  <div className={styles.progressBarTrack}>
                    <div
                      className={styles.progressBarFill}
                      style={{
                        width: `${pct}%`,
                        backgroundColor: sev.color,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Scans */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Recent Assessment Scans</h2>
            <Link to="/scans" className={styles.link} style={{ fontSize: '13px' }}>
              View all scans
            </Link>
          </div>

          {stats?.recent_scans && stats.recent_scans.length > 0 ? (
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Scan ID</th>
                    <th>Target</th>
                    <th>Profile</th>
                    <th>Status</th>
                    <th>Findings</th>
                    <th>Duration</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_scans.map((s) => (
                    <tr key={s.id}>
                      <td>#{s.id}</td>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {s.target ? s.target.name : `Target #${s.target_id}`}
                      </td>
                      <td>
                        <code style={{ fontSize: '12px' }}>{s.profile}</code>
                      </td>
                      <td>
                        <StatusBadge status={s.status} />
                      </td>
                      <td>{s.findings_count}</td>
                      <td>{s.duration != null ? `${s.duration}s` : '-'}</td>
                      <td>
                        <Link to={`/scans/${s.id}`} className={styles.link}>
                          Inspect →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              icon={Activity}
              title="No Scans Run Yet"
              description="Configure an authorized target and run your first assessment scan."
              action={
                <Link
                  to="/targets"
                  style={{
                    padding: '8px 16px',
                    background: 'var(--cyan-primary)',
                    color: '#000',
                    fontWeight: 600,
                    borderRadius: 'var(--radius-md)',
                    fontSize: '13px',
                  }}
                >
                  Create Target
                </Link>
              }
            />
          )}
        </div>
      </div>
    </div>
  );
}
