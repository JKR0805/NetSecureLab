import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  Crosshair,
  Activity,
  AlertTriangle,
  FileText,
  PlusCircle,
  Play,
  CheckCircle2,
} from 'lucide-react';
import api from '../../services/api';
import styles from './AppShell.module.css';

export function AppShell() {
  const [apiOnline, setApiOnline] = useState(false);
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
      } catch (err) {
        setApiOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const getPageTitle = () => {
    const p = location.pathname;
    if (p === '/') return 'Assessment Dashboard';
    if (p.startsWith('/targets')) return 'Target Assets & Scope';
    if (p.startsWith('/scans')) return 'Security Scans & Orchestration';
    if (p.startsWith('/findings')) return 'Security Findings';
    if (p.startsWith('/reports')) return 'Assessment Reports';
    return 'NetSecureLab';
  };

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/targets', label: 'Targets', icon: Crosshair },
    { to: '/scans', label: 'Scans', icon: Activity },
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
