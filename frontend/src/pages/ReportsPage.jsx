import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Download,
  Eye,
  RefreshCw,
} from 'lucide-react';
import { scanService } from '../services/scanService';
import { reportService } from '../services/reportService';
import { Modal } from '../components/common/Modal';
import { Loader, EmptyState } from '../components/common/Loader';
import styles from './TargetsPage.module.css';

export function ReportsPage() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [previewUrl, setPreviewUrl] = useState('');
  const [previewOpen, setPreviewOpen] = useState(false);
  const [generating, setGenerating] = useState(false);

  const fetchScans = async () => {
    try {
      setLoading(true);
      const data = await scanService.listScans();
      setScans(data.filter((s) => s.status === 'completed'));
    } catch (err) {
      console.error('Failed to load completed scans:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
  }, []);

  const handleGenerate = async (scanId) => {
    try {
      setGenerating(true);
      await reportService.generateReport(scanId);
      setPreviewUrl(reportService.getViewReportUrl(scanId));
      setPreviewOpen(true);
    } catch (err) {
      console.error('Failed to generate report:', err);
      alert('Report generation failed');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.topBar}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Generate structured, standalone HTML assessment reports including target profiles, discovered services, DNS records, evidence-backed findings, and methodology scope limitations.
          </p>
        </div>
        <button onClick={fetchScans} className={styles.actionBtn} style={{ padding: '8px' }}>
          <RefreshCw size={14} />
        </button>
      </div>

      <div className={styles.card}>
        {loading ? (
          <Loader text="Loading assessment reports..." />
        ) : scans.length > 0 ? (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Scan ID</th>
                <th>Target</th>
                <th>Profile</th>
                <th>Duration</th>
                <th>Findings</th>
                <th>Completed</th>
                <th>Report Actions</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.id}>
                  <td>
                    <strong>#{s.id}</strong>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {s.target ? s.target.name : `Target #${s.target_id}`}
                    </div>
                    {s.target && <code>{s.target.target}</code>}
                  </td>
                  <td>
                    <code>{s.profile}</code>
                  </td>
                  <td>{s.duration != null ? `${s.duration}s` : '-'}</td>
                  <td>
                    <strong>{s.findings_count}</strong>
                  </td>
                  <td>{s.completed_at ? new Date(s.completed_at).toLocaleDateString() : '-'}</td>
                  <td>
                    <div className={styles.actions}>
                      <button
                        onClick={() => handleGenerate(s.id)}
                        disabled={generating}
                        className={styles.actionBtn}
                        style={{
                          background: 'linear-gradient(135deg, var(--cyan-primary), #0284c7)',
                          color: '#fff',
                          fontWeight: 600,
                          border: 'none',
                        }}
                      >
                        <Eye size={13} />
                        View Report
                      </button>

                      <a
                        href={reportService.getDownloadReportUrl(s.id)}
                        download
                        className={styles.actionBtn}
                        title="Download HTML file"
                      >
                        <Download size={13} />
                        Download
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState
            icon={FileText}
            title="No Completed Assessments"
            description="Reports can be generated once an assessment scan completes."
            action={
              <Link
                to="/scans"
                className={styles.actionBtn}
                style={{
                  background: 'var(--cyan-primary)',
                  color: '#000',
                  fontWeight: 600,
                  marginTop: '12px',
                }}
              >
                Go to Scans
              </Link>
            }
          />
        )}
      </div>

      {/* Preview Modal */}
      <Modal
        isOpen={previewOpen}
        onClose={() => setPreviewOpen(false)}
        title="Assessment Report Preview"
        maxWidth="1000px"
        footer={
          <>
            <a
              href={previewUrl ? `${previewUrl}/download` : '#'}
              download
              className={styles.actionBtn}
              style={{ textDecoration: 'none' }}
            >
              <Download size={14} />
              Download HTML
            </a>
            <button
              onClick={() => setPreviewOpen(false)}
              className={styles.actionBtn}
              style={{ background: 'var(--cyan-primary)', color: '#000', fontWeight: 600 }}
            >
              Close Preview
            </button>
          </>
        }
      >
        <div style={{ height: '70vh', width: '100%' }}>
          {previewUrl && (
            <iframe
              src={previewUrl}
              title="Security Assessment Report"
              style={{ width: '100%', height: '100%', border: 'none', borderRadius: 'var(--radius-md)', background: '#fff' }}
            />
          )}
        </div>
      </Modal>
    </div>
  );
}
