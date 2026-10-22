import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  Crosshair,
  Activity,
  AlertTriangle,
  FileText,
  Play,
  Network,
  User as UserIcon,
} from 'lucide-react';
import api from '../../services/api';
import { authService } from '../../services/authService';
import styles from './AppShell.module.css';

export function AppShell() {
  const [apiOnline, setApiOnline] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const location = useLocation();

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.get('/health');
        if (res.data?.status === 'ok') {
          setApiOnline(true);
        } else {
          setApiOnline(false);
        }
      } catch {
        setApiOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);

    const initUser = async () => {
      let u = authService.getUser();
      if (!u) {
        try {
          const authRes = await authService.login('admin', 'NetSecureLab#2026!');
          u = authRes.user;
        } catch {
          // ignore if backend offline
        }
      }
      if (u) setCurrentUser(u);
    };
    initUser();

    return () => clearInterval(interval);
  }, []);

  const getPageTitle = () => {
    const p = location.pathname;
    if (p === '/') return 'Assessment Dashboard';
    if (p.startsWith('/targets')) return 'Target Assets & Scope';
    if (p.startsWith('/scans')) return 'Security Scans & Orchestration';
    if (p.startsWith('/topology')) return 'Network Topology Map';
    if (p.startsWith('/findings')) return 'Security Findings';
    if (p.startsWith('/reports')) return 'Assessment Reports';
    return 'NetSecureLab';
  };

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/targets', label: 'Targets', icon: Crosshair },
    { to: '/scans', label: 'Scans', icon: Activity },
    { to: '/topology', label: 'Topology', icon: Network },
    { to: '/findings', label: 'Findings', icon: AlertTriangle },
    { to: '/reports', label: 'Reports', icon: FileText },
  ];

  return (
    <div className={styles.layout}>
      {/* Sidebar Navigation */}
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <div className={styles.logoIcon}>
            <Shield size={22} />
          </div>
          <div className={styles.brandText}>
            <span className={styles.brandTitle}>NetSecureLab</span>
            <span className={styles.brandSubtitle}>Security Recon</span>
          </div>
        </div>

        <nav className={styles.nav}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  isActive ? `${styles.navItem} ${styles.navItemActive}` : styles.navItem
                }
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.statusIndicator}>
            <span
              className={`${styles.statusDot} ${!apiOnline ? styles.statusDotOffline : ''}`}
            />
            <span>{apiOnline ? 'Engine Online' : 'Connecting...'}</span>
          </div>
          <span className={styles.versionBadge}>v2.1</span>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className={styles.mainContent}>
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <h1 className={styles.pageTitle}>{getPageTitle()}</h1>
          </div>
          <div className={styles.headerActions}>
            {currentUser && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  padding: '6px 10px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  color: '#94a3b8',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <UserIcon size={13} color="#38bdf8" />
                <span style={{ color: '#f8fafc', fontWeight: 600 }}>{currentUser.username}</span>
                <span style={{ fontSize: '10px', textTransform: 'uppercase', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '1px 5px', borderRadius: '4px' }}>
                  {currentUser.role}
                </span>
              </div>
            )}
            <NavLink to="/targets" className={styles.btnSecondary}>
              <Crosshair size={15} />
              <span>Targets</span>
            </NavLink>
            <NavLink to="/scans" className={styles.btnPrimary}>
              <Play size={15} />
              <span>New Assessment</span>
            </NavLink>
          </div>
        </header>

        <main className={styles.pageContainer}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
