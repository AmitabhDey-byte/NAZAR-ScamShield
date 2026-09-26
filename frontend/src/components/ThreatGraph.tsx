import type { GraphEdge, GraphNode } from '../lib/types'

const typeColors: Record<string, string> = {
  PHONE: '#76a7c9', UPI: '#dfbd7a', DOMAIN: '#ef6b59', URL: '#ef6b59', CAMPAIGN: '#b99055',
  MESSAGE_PATTERN: '#979b94', CLAIMED_ORGANIZATION: '#72c98b',
}

export function ThreatGraph({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  const limited = nodes.slice(0, 12)
  const positions = limited.map((node, index) => {
    const angle = (index / limited.length) * Math.PI * 2 - Math.PI / 2
    const radius = node.type === 'CAMPAIGN' ? 0 : index % 2 ? 155 : 230
    return { ...node, x: 390 + Math.cos(angle) * radius, y: 270 + Math.sin(angle) * radius }
  })
  const pos = new Map(positions.map(node => [node.id, node]))
  return (
    <div className="graph-canvas" role="img" aria-label="Connected scam indicators and campaigns">
      <svg viewBox="0 0 780 540" preserveAspectRatio="xMidYMid meet">
        <defs><filter id="glow"><feGaussianBlur stdDeviation="4" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter></defs>
        {edges.map((edge, index) => {
          const source = pos.get(edge.source); const target = pos.get(edge.target)
          if (!source || !target) return null
          return <g key={`${edge.source}-${edge.target}-${index}`}><line x1={source.x} y1={source.y} x2={target.x} y2={target.y} className="graph-edge" /><text x={(source.x + target.x) / 2} y={(source.y + target.y) / 2 - 5} className="edge-label">{edge.type.replaceAll('_', ' ')}</text></g>
        })}
        {positions.map(node => <g key={node.id} transform={`translate(${node.x},${node.y})`} className="graph-node"><circle r={node.type === 'CAMPAIGN' ? 46 : 30} fill={`${typeColors[node.type] || '#979b94'}22`} stroke={typeColors[node.type] || '#979b94'} filter="url(#glow)" /><text y="-3" textAnchor="middle" className="node-type">{node.type}</text><text y="14" textAnchor="middle" className="node-label">{String(node.label || node.value || '').slice(0, 18)}</text></g>)}
      </svg>
    </div>
  )
}

