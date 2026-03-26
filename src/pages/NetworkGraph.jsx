import React, { useState, useEffect, useCallback, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import * as d3 from 'd3';
import './NetworkGraph.css';

const NetworkGraph = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [stats, setStats] = useState({ nodes: 0, links: 0, industries: 0 });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const fgRef = useRef();

  const getColor = (industry) => {
    const map = {
      'Steel': '#7f8c8d',
      'Aluminum': '#bdc3c7',
      'Plastics': '#3498db',
      'Agriculture': '#27ae60',
      'Food Processing': '#2ecc71',
      'Construction': '#95a5a6',
      'Manufacturing': '#34495e',
      'Chemicals': '#e67e22',
      'Electronics': '#e74c3c',
      'Textiles': '#f1c40f',
      'Renewable Energy': '#1abc9c'
    };
    return map[industry] || '#9b59b6';
  };

  const fetchGraphData = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const userId = user.id;
      const response = await fetch(`/api/network/graph?user_id=${userId || ''}`);
      const data = await response.json();
      
      // Fix logged-in user to center
      const processedNodes = data.nodes.map(node => {
        if (String(node.id) === String(userId)) {
          return { ...node, fx: 0, fy: 0 };
        }
        return node;
      });

      // Add multi-link handling (assign indices to links between same nodes)
      const linkMap = {};
      const processedLinks = data.links.map(link => {
        const key = [link.source, link.target].sort().join('-');
        linkMap[key] = (linkMap[key] || 0) + 1;
        return { ...link, linkNum: linkMap[key] };
      });

      setGraphData({ ...data, nodes: processedNodes, links: processedLinks });
      setStats({
        nodes: data.nodes.length,
        links: data.links.length,
        industries: new Set(data.nodes.map(n => n.industry)).size
      });

      // Apply improved forces
      if (fgRef.current) {
        fgRef.current.d3Force('charge').strength(-400);
        fgRef.current.d3Force('link').distance(150);
        fgRef.current.d3Force('center', d3.forceCenter(0, 0));
      }
    } catch (error) {
      console.error('Error fetching graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
    const interval = setInterval(fetchGraphData, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(2.5, 1000);
    }
  };

  if (loading && graphData.nodes.length === 0) {
    return (
      <div className="network-loading">
        <div className="loader"></div>
        <p>Initializing Neural Supply Chain...</p>
      </div>
    );
  }

  return (
    <div className="network-container">
      <div className="network-header">
        <div className="header-content">
          <div className="title-section">
            <h1>Industrial Network</h1>
            <p>Live supply chain connections & ecosystem health</p>
          </div>
          <div className="stats-row">
            <div className="stat-pill">
              <span className="dot pulse"></span>
              <strong>{stats.nodes}</strong> Companies
            </div>
            <div className="stat-pill">
              <strong>{stats.links}</strong> Pathways
            </div>
            <div className="stat-pill">
              <strong>{stats.industries}</strong> Industries
            </div>
          </div>
        </div>
      </div>

      <div className="graph-wrapper">
        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          nodeLabel={(node) => `${node.name} (${node.industry})`}
          nodeColor={(node) => getColor(node.industry)}
          nodeRelSize={6}
          // Link enhancements
          linkCurvature={(link) => {
            const numLinks = graphData.links.filter(l => 
                (l.source === link.source && l.target === link.target) ||
                (l.source === link.target && l.target === link.source)
            ).length;
            if (numLinks <= 1) return 0;
            return (link.linkNum - (numLinks + 1) / 2) * (1 / numLinks);
          }}
          linkDirectionalParticles={(link) => {
            if (link.relationship === 'CHATTED_WITH') return 4;
            if (link.relationship === 'DEALT_WITH') return 2;
            return 0;
          }}
          linkLabel={(link) => `<div class="link-label">${link.relationship.replace(/_/g, ' ')} ${link.waste_type ? `(${link.waste_type})` : ''}</div>`}
          linkColor={(link) => {
            if (link.relationship === 'DEALT_WITH') return 'rgba(16, 185, 129, 0.4)'; // Fainter Green
            if (link.relationship === 'CHATTED_WITH') return 'rgba(59, 130, 246, 0.4)'; // Fainter Blue
            return 'rgba(255, 255, 255, 0.1)'; // Fainter Default
          }}
          onNodeClick={handleNodeClick}
          cooldownTicks={100}
          backgroundColor="#0f172a"
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 11 / globalScale;
            ctx.font = `${fontSize}px Inter, sans-serif`;
            
            // Draw Node Circle
            ctx.beginPath();
            ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI, false);
            ctx.fillStyle = getColor(node.industry);
            ctx.fill();
            
            // Highlight Logged-in User
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            const userId = user.id;
            if (userId && String(node.id) === String(userId)) {
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 4 / globalScale;
                ctx.stroke();
                
                // Pulsing ring for center node
                const t = Date.now() / 500;
                const r = 10 + Math.sin(t) * 2;
                ctx.beginPath();
                ctx.arc(node.x, node.y, r / globalScale, 0, 2 * Math.PI);
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
                ctx.lineWidth = 1 / globalScale;
                ctx.stroke();
            }

            // Outer ring for selected node
            if (selectedNode && selectedNode.id === node.id) {
                ctx.strokeStyle = '#3b82f6';
                ctx.lineWidth = 3 / globalScale;
                ctx.stroke();
            }

            // Draw Label - Only when zoomed in
            if (globalScale > 1.8) {
                ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(label, node.x, node.y + (14 / globalScale));
                
                // Industry Label
                ctx.font = `${8 / globalScale}px Inter`;
                ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
                ctx.fillText(node.industry, node.x, node.y + (22 / globalScale));
            }
          }}
          // Draw labels on links - Zoom threshold increased
          linkCanvasObjectMode={() => 'after'}
          linkCanvasObject={(link, ctx, globalScale) => {
            if (globalScale < 2.5) return; // Much higher threshold

            const MAX_FONT_SIZE = 3 / globalScale;
            const start = link.source;
            const end = link.target;

            if (typeof start !== 'object' || typeof end !== 'object') return;

            const textPos = {
              x: start.x + (end.x - start.x) * 0.5,
              y: start.y + (end.y - start.y) * 0.5
            };

            const relLink = { x: end.x - start.x, y: end.y - start.y };
            let textAngle = Math.atan2(relLink.y, relLink.x);
            if (textAngle > Math.PI / 2) textAngle = -(Math.PI - textAngle);
            if (textAngle < -Math.PI / 2) textAngle = -(-Math.PI - textAngle);

            const label = link.relationship.replace(/_/g, ' ');

            ctx.save();
            ctx.translate(textPos.x, textPos.y);
            ctx.rotate(textAngle);
            ctx.font = `${8 / globalScale}px Inter`;
            ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(label, 0, -2);
            ctx.restore();
          }}
        />
      </div>

      {selectedNode && (
        <div className="node-details-panel">
          <button className="close-btn" onClick={() => setSelectedNode(null)}>&times;</button>
          <div className="panel-header">
             <div className="avatar" style={{ backgroundColor: getColor(selectedNode.industry) }}>
                {selectedNode.name[0]}
             </div>
             <h2>{selectedNode.name}</h2>
             <span className="industry-tag">{selectedNode.industry}</span>
          </div>
          <div className="panel-body">
            <div className="detail-item">
              <label>Location</label>
              <p>{selectedNode.location}</p>
            </div>
            <div className="detail-row-stats">
                <div className="detail-stat">
                    <label>Deals</label>
                    <p>{selectedNode.deal_count || 0}</p>
                </div>
                <div className="detail-stat">
                    <label>Chats</label>
                    <p>{selectedNode.chat_count || 0}</p>
                </div>
                <div className="detail-stat">
                    <label>Batches</label>
                    <p>{selectedNode.classifications || 0}</p>
                </div>
            </div>
            <div className="detail-row">
                <button className="action-btn" onClick={() => window.location.href=`/chat?partner=${selectedNode.id}`}>
                    Message Company
                </button>
            </div>
          </div>
        </div>
      )}

      <div className="graph-legend">
        <h4>Industries</h4>
        <div className="legend-items">
             {['Steel', 'Plastics', 'Agriculture', 'Manufacturing', 'Electronics'].map(i => (
                 <div key={i} className="legend-item">
                     <span className="color-dot" style={{ backgroundColor: getColor(i) }}></span>
                     {i}
                 </div>
             ))}
        </div>
      </div>
    </div>
  );
};

export default NetworkGraph;
