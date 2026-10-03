import React from 'react';
import { Loader2 } from 'lucide-react';

export function Loader({ text = 'Loading data...', size = 24 }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        color: 'var(--text-muted)',
        gap: '12px',
      }}
    >
      <Loader2
        size={size}
        style={{
          color: 'var(--cyan-primary)',
          animation: 'spin 1s linear infinite',
        }}
      />
      <span style={{ fontSize: '14px', fontWeight: 500 }}>{text}</span>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '56px 24px',
        textAlign: 'center',
        border: '1px dashed var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        background: 'rgba(15, 23, 42, 0.4)',
        margin: '16px 0',
      }}
    >
      {Icon && (
        <div
          style={{
            width: '52px',
            height: '52px',
            borderRadius: '50%',
            background: 'rgba(6, 182, 212, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--cyan-primary)',
            marginBottom: '16px',
          }}
        >
          <Icon size={26} />
        </div>
      )}
      <h3 style={{ fontSize: '17px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
        {title}
      </h3>
      <p style={{ fontSize: '14px', color: 'var(--text-muted)', maxWidth: '440px', marginBottom: action ? '20px' : '0' }}>
        {description}
      </p>
      {action}
    </div>
  );
}
