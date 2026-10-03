import React from 'react';

export function SeverityBadge({ severity }) {
  const sev = (severity || 'informational').toLowerCase();
  
  const styles = {
    high: {
      bg: 'var(--sev-high-bg)',
      border: 'var(--sev-high-border)',
      color: 'var(--sev-high-text)',
    },
    medium: {
      bg: 'var(--sev-med-bg)',
      border: 'var(--sev-med-border)',
      color: 'var(--sev-med-text)',
    },
    low: {
      bg: 'var(--sev-low-bg)',
      border: 'var(--sev-low-border)',
      color: 'var(--sev-low-text)',
    },
    informational: {
      bg: 'var(--sev-info-bg)',
      border: 'var(--sev-info-border)',
      color: 'var(--sev-info-text)',
    },
  }[sev] || {
    bg: 'var(--sev-info-bg)',
    border: 'var(--sev-info-border)',
    color: 'var(--sev-info-text)',
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '3px 8px',
        fontSize: '11px',
        fontWeight: '600',
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        borderRadius: 'var(--radius-full)',
        backgroundColor: styles.bg,
        border: `1px solid ${styles.border}`,
        color: styles.color,
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: styles.color,
        }}
      />
      {sev}
    </span>
  );
}

export function StatusBadge({ status }) {
  const stat = (status || 'pending').toLowerCase();

  const getStyle = () => {
    switch (stat) {
      case 'completed':
      case 'success':
        return { bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.4)', color: '#34d399' };
      case 'running':
        return { bg: 'rgba(6, 182, 212, 0.15)', border: 'rgba(6, 182, 212, 0.4)', color: '#38bdf8', pulse: true };
      case 'queued':
      case 'pending':
        return { bg: 'rgba(168, 85, 247, 0.15)', border: 'rgba(168, 85, 247, 0.4)', color: '#c084fc' };
      case 'partial':
        return { bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.4)', color: '#fbbf24' };
      case 'failed':
        return { bg: 'rgba(244, 63, 94, 0.15)', border: 'rgba(244, 63, 94, 0.4)', color: '#fb7185' };
      case 'cancelled':
      case 'skipped':
      default:
        return { bg: 'rgba(100, 116, 139, 0.15)', border: 'rgba(100, 116, 139, 0.4)', color: '#94a3b8' };
    }
  };

  const style = getStyle();

  return (
    <span
      className={style.pulse ? 'pulsing-indicator' : ''}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '3px 10px',
        fontSize: '11px',
        fontWeight: '600',
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        borderRadius: 'var(--radius-full)',
        backgroundColor: style.bg,
        border: `1px solid ${style.border}`,
        color: style.color,
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: style.color,
        }}
      />
      {stat}
    </span>
  );
}
