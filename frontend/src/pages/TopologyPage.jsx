import React, { useState, useEffect, useMemo } from 'react';
import {
  Network,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Shield,
  Server,
  Cpu,
  AlertTriangle,
  X,
} from 'lucide-react';
import { topologyService } from '../services/topologyService';
import { targetService } from '../services/targetService';
import { SeverityBadge } from '../components/common/Badge';
import styles from './TopologyPage.module.css';

export function TopologyPage() {
  const [data, setData] = useState({ nodes: [], links: [], stats: {} });
  const [targets, setTargets] = useState([]);
  const [selectedTargetId, setSelectedTargetId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const [zoom, setZoom] = useState(1);

  // Filter toggles
  const [showServices, setShowServices] = useState(true);
  const [showVulns, setShowVulns] = useState(true);

  const fetchTargetsList = async () => {
    try {
      const res = await targetService.getTargets();
      setTargets(res.items || res || []);
    } catch {
      // Non-critical, ignore
    }
  };

  const fetchTopology = async (targetId = null) => {
    setLoading(true);
    setError(null);
    try {
      const res = await topologyService.getTopology(targetId || null);
      setData(res);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load network topology graph.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTargetsList();
  }, []);

  useEffect(() => {
    fetchTopology(selectedTargetId ? Number(selectedTargetId) : null);
  }, [selectedTargetId]);

  // Layout calculation
  const layout = useMemo(() => {
    const rawNodes = data.nodes || [];
    const rawLinks = data.links || [];

    // Filter nodes based on user toggle
    const visibleNodes = rawNodes.filter((node) => {
      if (!showServices && node.type === 'service') return false;
      if (!showVulns && node.type === 'vulnerability') return false;
      return true;
    });

    const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));
    const visibleLinks = rawLinks.filter(
      (l) => visibleNodeIds.has(l.source) && visibleNodeIds.has(l.target)
    );

    // Group into columns
    const cols = {
      target: [],
      host: [],
      service: [],
      vulnerability: [],
    };

    visibleNodes.forEach((node) => {
      if (cols[node.type]) {
        cols[node.type].push(node);
      }
    });

    const colX = {
      target: 80,
      host: 360,
      service: 660,
      vulnerability: 980,
    };

    const maxItems = Math.max(
      cols.target.length,
      cols.host.length,
      cols.service.length,
      cols.vulnerability.length,
      5
    );

    const canvasWidth = 1280;
    const canvasHeight = Math.max(650, maxItems * 80 + 100);

    const positionedNodes = {};

    Object.entries(cols).forEach(([type, nodesInCol]) => {
      const startX = colX[type];
      const count = nodesInCol.length;
      const spacing = count > 1 ? (canvasHeight - 140) / Math.max(count, 1) : 0;

      nodesInCol.forEach((node, idx) => {
        const y = count === 1 ? canvasHeight / 2 : 80 + idx * spacing;
        positionedNodes[node.id] = {
          ...node,
          x: startX,
          y,
        };
      });
    });

    return {
      nodes: Object.values(positionedNodes),
      nodeMap: positionedNodes,
      links: visibleLinks,
      width: canvasWidth,
      height: canvasHeight,
    };
  }, [data, showServices, showVulns]);

  const filteredNodes = useMemo(() => {
    if (!searchQuery.trim()) return layout.nodes;
    const q = searchQuery.toLowerCase();
    return layout.nodes.filter(
      (n) =>
        n.label?.toLowerCase().includes(q) ||
        n.ip?.toLowerCase().includes(q) ||
        n.service?.toLowerCase().includes(q)
    );
  }, [layout.nodes, searchQuery]);

  const searchMatchingIds = useMemo(() => {
    return new Set(filteredNodes.map((n) => n.id));
  }, [filteredNodes]);

  const getNodeColor = (node) => {
    if (node.type === 'target') return '#0284c7';
    if (node.type === 'host') return '#3b82f6';
    if (node.type === 'service') return '#10b981';
    if (node.type === 'vulnerability') {
      if (node.severity === 'high' || node.severity === 'critical') return '#ef4444';
      if (node.severity === 'medium') return '#f59e0b';
      return '#38bdf8';
    }
    return '#64748b';
  };

  return (
    <div className={styles.container}>
      {/* Header & Controls */}
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <h1>Network Topology Map</h1>
          <p>Visualizing discovered perimeter assets, exposed network ports, and vulnerability graph</p>
        </div>

        <div className={styles.controlsBar}>
          <select
            className={styles.selectInput}
            value={selectedTargetId}
            onChange={(e) => setSelectedTargetId(e.target.value)}
          >
            <option value="">All Targets</option>
            {targets.map((t) => (
              <option key={t.id} value={t.id}>
                {t.value} ({t.type})
              </option>
            ))}
          </select>

          <div style={{ position: 'relative' }}>
            <input
              type="text"
              placeholder="Search nodes..."
              className={styles.searchInput}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <button
            className={styles.ctrlBtn}
            onClick={() => fetchTopology(selectedTargetId ? Number(selectedTargetId) : null)}
            title="Refresh Map"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Stats Bar & Display Toggles */}
      <div className={styles.statsBar}>
        <div className={styles.statItem}>
          <Shield size={14} color="#0284c7" />
          <span>Targets:</span>
          <span className={styles.statValue}>{data.stats?.targets || 0}</span>
        </div>
        <div className={styles.statItem}>
          <Server size={14} color="#3b82f6" />
          <span>Discovered Hosts:</span>
          <span className={styles.statValue}>{data.stats?.hosts || 0}</span>
        </div>
        <div className={styles.statItem}>
          <Cpu size={14} color="#10b981" />
          <span>Active Services:</span>
          <span className={styles.statValue}>{data.stats?.services || 0}</span>
        </div>
        <div className={styles.statItem}>
          <AlertTriangle size={14} color="#ef4444" />
          <span>Vulnerabilities:</span>
          <span className={styles.statValue}>{data.stats?.vulnerabilities || 0}</span>
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showServices}
              onChange={(e) => setShowServices(e.target.checked)}
            />
            Show Services
          </label>
          <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showVulns}
              onChange={(e) => setShowVulns(e.target.checked)}
            />
            Show Vulnerabilities
          </label>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className={styles.mainArea}>
        {loading ? (
          <div className={styles.emptyState}>
            <RefreshCw size={32} className="spin" />
            <p>Constructing network topology graph...</p>
          </div>
        ) : error ? (
          <div className={styles.emptyState}>
            <AlertTriangle size={32} color="#ef4444" />
            <p>{error}</p>
          </div>
        ) : layout.nodes.length === 0 ? (
          <div className={styles.emptyState}>
            <Network size={40} />
            <h3>No Network Assets Discovered</h3>
            <p>Add a scope target and run an assessment scan to map out your infrastructure.</p>
          </div>
        ) : (
          <div className={styles.canvasWrapper}>
            {/* Zoom Controls */}
            <div className={styles.canvasControls}>
              <button
                className={styles.ctrlBtn}
                onClick={() => setZoom((z) => Math.min(z + 0.15, 2.0))}
                title="Zoom In"
              >
                <ZoomIn size={16} />
              </button>
              <button
                className={styles.ctrlBtn}
                onClick={() => setZoom((z) => Math.max(z - 0.15, 0.5))}
                title="Zoom Out"
              >
                <ZoomOut size={16} />
              </button>
              <button
                className={styles.ctrlBtn}
                onClick={() => setZoom(1)}
                title="Reset Zoom"
              >
                <RotateCcw size={16} />
              </button>
            </div>

            <svg
              className={styles.canvasSvg}
              width={layout.width * zoom}
              height={layout.height * zoom}
              viewBox={`0 0 ${layout.width} ${layout.height}`}
            >
              <defs>
                <linearGradient id="linkGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#818cf8" stopOpacity="0.4" />
                </linearGradient>
              </defs>

              {/* Render Links */}
              {layout.links.map((link, idx) => {
                const src = layout.nodeMap[link.source];
                const dst = layout.nodeMap[link.target];
                if (!src || !dst) return null;

                const x1 = src.x + 80;
                const y1 = src.y;
                const x2 = dst.x - 80;
                const y2 = dst.y;
                const mx = (x1 + x2) / 2;

                const pathData = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;

                const isHighlighted =
                  selectedNode &&
                  (selectedNode.id === src.id || selectedNode.id === dst.id);

                return (
                  <path
                    key={`link-${link.source}-${link.target}-${idx}`}
                    d={pathData}
                    fill="none"
                    stroke={isHighlighted ? '#38bdf8' : 'url(#linkGrad)'}
                    strokeWidth={isHighlighted ? 2.5 : 1.5}
                    strokeDasharray={link.relation === 'vulnerability_in' ? '4,4' : 'none'}
                    opacity={isHighlighted ? 1 : 0.6}
                  />
                );
              })}

              {/* Render Nodes */}
              {layout.nodes.map((node) => {
                const isSelected = selectedNode?.id === node.id;
                const isMatched = searchQuery
                  ? searchMatchingIds.has(node.id)
                  : true;
                const color = getNodeColor(node);

                return (
                  <g
                    key={node.id}
                    transform={`translate(${node.x}, ${node.y})`}
                    className={styles[`node${node.type.charAt(0).toUpperCase() + node.type.slice(1)}`]}
                    onClick={() => setSelectedNode(node)}
                    opacity={isMatched ? 1 : 0.25}
                  >
                    {/* Node background card */}
                    <rect
                      x={-75}
                      y={-22}
                      width={150}
                      height={44}
                      rx={8}
                      fill="#0f172a"
                      stroke={isSelected ? '#38bdf8' : color}
                      strokeWidth={isSelected ? 2 : 1.2}
                    />

                    {/* Node status dot */}
                    <circle cx={-60} cy={0} r={4} fill={color} />

                    {/* Node label */}
                    <text
                      x={-48}
                      y={-3}
                      fill="#f8fafc"
                      fontSize={11}
                      fontWeight="600"
                      fontFamily="system-ui, sans-serif"
                    >
                      {node.label && node.label.length > 17
                        ? `${node.label.slice(0, 16)}…`
                        : node.label}
                    </text>

                    {/* Subtitle / Type */}
                    <text
                      x={-48}
                      y={12}
                      fill="#94a3b8"
                      fontSize={9}
                      fontFamily="system-ui, sans-serif"
                    >
                      {node.type === 'service'
                        ? node.state
                        : node.type === 'vulnerability'
                        ? node.severity.toUpperCase()
                        : node.type.toUpperCase()}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        )}

        {/* Selected Node Details Drawer */}
        {selectedNode && (
          <aside className={styles.sideDrawer}>
            <div className={styles.drawerHeader}>
              <span className={styles.drawerTitle}>
                {selectedNode.type.toUpperCase()} DETAILS
              </span>
              <button
                className={styles.closeBtn}
                onClick={() => setSelectedNode(null)}
              >
                <X size={16} />
              </button>
            </div>

            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Name / Label</span>
              <span className={styles.detailValue} style={{ fontWeight: 600 }}>
                {selectedNode.label}
              </span>
            </div>

            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Type</span>
              <span className={styles.detailValue}>{selectedNode.type}</span>
            </div>

            {selectedNode.type === 'target' && (
              <>
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Target Scope Type</span>
                  <span className={styles.detailValue}>{selectedNode.target_type}</span>
                </div>
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Authorization</span>
                  <span className={styles.detailValue}>
                    {selectedNode.authorization_confirmed ? 'Authorized' : 'Pending Authorization'}
                  </span>
                </div>
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Description</span>
                  <span className={styles.detailValue}>
                    {selectedNode.description || 'No description provided'}
                  </span>
                </div>
              </>
            )}

            {selectedNode.type === 'host' && (
              <>
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>IP Address</span>
                  <span className={styles.detailValue}>{selectedNode.ip}</span>
                </div>
                {selectedNode.hostname && (
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>Hostname</span>
                    <span className={styles.detailValue}>{selectedNode.hostname}</span>
                  </div>
                )}
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Operating System</span>
                  <span className={styles.detailValue}>{selectedNode.os}</span>
                </div>
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Host Status</span>
                  <span className={styles.detailValue}>{selectedNode.status}</span>
                </div>
              </>
            )}

            {selectedNode.type === 'service' && (
              <>
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Port / Protocol</span>
                  <span className={styles.detailValue}>
                    {selectedNode.port_number}/{selectedNode.protocol}
                  </span>
                </div>
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Identified Service</span>
                  <span className={styles.detailValue}>{selectedNode.service}</span>
                </div>
                {selectedNode.product && (
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>Software Product</span>
                    <span className={styles.detailValue}>{selectedNode.product}</span>
                  </div>
                )}
                {selectedNode.version && (
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>Version</span>
                    <span className={styles.detailValue}>{selectedNode.version}</span>
                  </div>
                )}
              </>
            )}

            {selectedNode.type === 'vulnerability' && (
              <>
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Severity</span>
                  <div>
                    <SeverityBadge severity={selectedNode.severity} />
                  </div>
                </div>
                {selectedNode.rule_id && (
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>Rule ID</span>
                    <span className={styles.detailValue}>{selectedNode.rule_id}</span>
                  </div>
                )}
                {selectedNode.source && (
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>Detection Source</span>
                    <span className={styles.detailValue}>{selectedNode.source.toUpperCase()}</span>
                  </div>
                )}
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Status</span>
                  <span className={styles.detailValue}>{selectedNode.status}</span>
                </div>
              </>
            )}
          </aside>
        )}
      </div>
    </div>
  );
}
