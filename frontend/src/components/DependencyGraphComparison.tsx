import { useEffect, useRef, useState } from 'react';
import {
  Box, Typography, Paper, Grid, Chip, CircularProgress, Alert,
  Divider, Tooltip, LinearProgress,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  AccountTree as GraphIcon,
  SwapHoriz as SwapIcon,
} from '@mui/icons-material';
import { api, type DependencyGraphsResponse, type DependencyGraph } from '../api';

interface Props { projectId: string; }

// ── Colour palette ─────────────────────────────────────────────────────────────
const NODE_COLOR: Record<string, string> = {
  file: '#42a5f5',
  class: '#66bb6a',
  function: '#ffa726',
  module: '#ab47bc',
};
const EDGE_COLOR: Record<string, string> = {
  import: '#90caf9',
  contains: '#a5d6a7',
  inheritance: '#ffcc80',
  call: '#ce93d8',
  circular: '#ef9a9a',
};

// ── Deterministic layout ───────────────────────────────────────────────────────
// Both graphs use the same algorithm so they look structurally alike.
// File nodes are placed in a circle; class nodes orbit their parent file.
interface LayoutNode { id: string; x: number; y: number; type: string; name: string; }
interface LayoutEdge { source: string; target: string; type: string; }

function buildLayout(
  graph: DependencyGraph,
  W: number,
  H: number,
): { nodes: LayoutNode[]; edges: LayoutEdge[] } {
  const fileNodes = graph.nodes.filter(n => n.type === 'file').slice(0, 50);
  const classNodes = graph.nodes.filter(n => n.type === 'class').slice(0, 40);
  const shownIds = new Set([...fileNodes, ...classNodes].map(n => n.id));

  const cx = W / 2, cy = H / 2;
  const outerR = Math.min(cx, cy) - 22;
  const posMap: Record<string, { x: number; y: number }> = {};

  // File nodes on outer circle
  fileNodes.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / Math.max(fileNodes.length, 1) - Math.PI / 2;
    posMap[n.id] = { x: cx + outerR * Math.cos(angle), y: cy + outerR * Math.sin(angle) };
  });

  // Class nodes on inner circle (smaller radius)
  const innerR = outerR * 0.52;
  classNodes.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / Math.max(classNodes.length, 1) - Math.PI / 2;
    posMap[n.id] = { x: cx + innerR * Math.cos(angle), y: cy + innerR * Math.sin(angle) };
  });

  const layoutNodes: LayoutNode[] = [...fileNodes, ...classNodes].map(n => ({
    id: n.id,
    x: posMap[n.id]?.x ?? cx,
    y: posMap[n.id]?.y ?? cy,
    type: n.type,
    name: n.name || n.id.split('/').pop()?.split('\\').pop() || n.id,
  }));

  const layoutEdges: LayoutEdge[] = graph.edges
    .filter(e => shownIds.has(e.source) && shownIds.has(e.target) && e.source !== e.target)
    .slice(0, 100)
    .map(e => ({ source: e.source, target: e.target, type: e.type }));

  return { nodes: layoutNodes, edges: layoutEdges };
}

// ── Canvas renderer ────────────────────────────────────────────────────────────
function GraphCanvas({
  graph,
  label,
  emptyMessage = 'No graph data',
}: {
  graph: DependencyGraph | null | undefined;
  label: string;
  emptyMessage?: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const W = 340, H = 240;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, W, H);

    const hasNodes = graph?.nodes?.length;
    if (!hasNodes) {
      ctx.fillStyle = '#bbb';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(emptyMessage, W / 2, H / 2);
      return;
    }

    const { nodes, edges } = buildLayout(graph!, W, H);
    const posMap: Record<string, { x: number; y: number }> = {};
    for (const n of nodes) posMap[n.id] = { x: n.x, y: n.y };

    // Edges
    for (const e of edges) {
      const s = posMap[e.source], t = posMap[e.target];
      if (!s || !t) continue;
      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.strokeStyle = EDGE_COLOR[e.type] ?? '#ccc';
      ctx.lineWidth = e.type === 'inheritance' ? 1.5 : 0.9;
      ctx.globalAlpha = 0.45;
      ctx.stroke();
    }
    ctx.globalAlpha = 1;

    // Nodes
    for (const n of nodes) {
      const p = posMap[n.id];
      if (!p) continue;
      const r = n.type === 'file' ? 6 : 4;
      ctx.beginPath();
      ctx.arc(p.x, p.y, r, 0, 2 * Math.PI);
      ctx.fillStyle = NODE_COLOR[n.type] ?? '#90a4ae';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    // Bottom label
    ctx.fillStyle = '#777';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(label, W / 2, H - 4);
  }, [graph, label, emptyMessage]);

  return (
    <canvas
      ref={canvasRef}
      width={W}
      height={H}
      style={{ borderRadius: 8, background: '#f5f7fa', display: 'block', width: '100%', height: 'auto' }}
    />
  );
}

// ── Legend ─────────────────────────────────────────────────────────────────────
function Legend() {
  return (
    <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', mt: 0.75 }}>
      {Object.entries(NODE_COLOR).map(([type, color]) => (
        <Box key={type} sx={{ display: 'flex', alignItems: 'center', gap: 0.4 }}>
          <Box sx={{ width: 9, height: 9, borderRadius: '50%', bgcolor: color, flexShrink: 0 }} />
          <Typography variant="caption" color="text.secondary">{type}</Typography>
        </Box>
      ))}
    </Box>
  );
}

// ── Score bar ──────────────────────────────────────────────────────────────────
function ScoreBar({ label, value, tip }: { label: string; value: number; tip?: string }) {
  const color = value >= 70 ? '#4caf50' : value >= 45 ? '#ff9800' : '#f44336';
  const inner = (
    <Box sx={{ mb: 1.5 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.4 }}>
        <Typography variant="body2" color="text.secondary">{label}</Typography>
        <Typography variant="body2" fontWeight={700} sx={{ color }}>{value.toFixed(1)}%</Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={Math.min(value, 100)}
        sx={{ height: 7, borderRadius: 4, bgcolor: '#e0e0e0', '& .MuiLinearProgress-bar': { bgcolor: color, borderRadius: 4 } }}
      />
    </Box>
  );
  return tip ? <Tooltip title={tip} placement="top">{inner}</Tooltip> : inner;
}

// ── Metric diff row ────────────────────────────────────────────────────────────
function MetricRow({ label, orig, conv }: { label: string; orig: number; conv: number }) {
  const delta = conv - orig;
  const dc = delta === 0 ? 'text.disabled' : delta > 0 ? 'warning.main' : 'success.main';
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 0.35 }}>
      <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>{label}</Typography>
      <Box sx={{ display: 'flex', gap: 1.5, minWidth: 130, justifyContent: 'flex-end' }}>
        <Typography variant="body2" sx={{ minWidth: 34, textAlign: 'right' }}>{orig}</Typography>
        <Typography variant="body2" sx={{ minWidth: 34, textAlign: 'right' }}>{conv}</Typography>
        <Typography variant="body2" sx={{ minWidth: 38, textAlign: 'right', color: dc, fontWeight: 600 }}>
          {delta === 0 ? '—' : `${delta > 0 ? '+' : ''}${delta}`}
        </Typography>
      </Box>
    </Box>
  );
}

// ── Status badge ───────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: 'pass' | 'warn' | 'fail' }) {
  if (status === 'pass') return <Chip icon={<CheckCircleIcon />} label="Validation Passed" color="success" size="small" />;
  if (status === 'warn') return <Chip icon={<WarningIcon />} label="Minor Differences" color="warning" size="small" />;
  return <Chip icon={<ErrorIcon />} label="Structural Mismatch" color="error" size="small" />;
}

// ── Metric chips under each graph ──────────────────────────────────────────────
function GraphChips({ m }: { m: Record<string, number> }) {
  return (
    <Box sx={{ mt: 0.75, display: 'flex', gap: 0.6, flexWrap: 'wrap' }}>
      <Chip label={`${m.file_nodes ?? 0} files`} size="small" variant="outlined" />
      <Chip label={`${m.class_nodes ?? 0} classes`} size="small" variant="outlined" />
      <Chip label={`${m.function_nodes ?? 0} fns`} size="small" variant="outlined" />
      {(m.import_edges ?? 0) > 0 && <Chip label={`${m.import_edges} imports`} size="small" variant="outlined" />}
      {(m.circular_dependencies ?? 0) > 0 && (
        <Chip label={`${m.circular_dependencies} cycles`} size="small" color="warning" />
      )}
    </Box>
  );
}

// ── Main ───────────────────────────────────────────────────────────────────────
export default function DependencyGraphComparison({ projectId }: Props) {
  const [data, setData] = useState<DependencyGraphsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.getDependencyGraphs(projectId)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 5 }}><CircularProgress size={36} /></Box>;
  if (error) return <Alert severity="error">{error}</Alert>;
  if (!data) return null;

  const { initial_graph, converted_graph, comparison: cmp, has_converted } = data;
  const origM = (initial_graph?.metrics ?? {}) as unknown as Record<string, number>;
  const convM = (converted_graph?.metrics ?? {}) as unknown as Record<string, number>;

  const origLabel = `${origM.file_nodes ?? 0} files · ${origM.import_edges ?? 0} imports`;
  const convLabel = `${convM.file_nodes ?? 0} files · ${convM.import_edges ?? 0} imports`;

  const bannerBg = !cmp ? '#fff' : cmp.validation_status === 'pass' ? '#e8f5e9' : cmp.validation_status === 'warn' ? '#fff8e1' : '#ffebee';
  const bannerBorder = !cmp ? 'divider' : cmp.validation_status === 'pass' ? 'success.light' : cmp.validation_status === 'warn' ? 'warning.light' : 'error.light';

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
        <GraphIcon color="primary" />
        <Typography variant="h6">Dependency Graph Validation</Typography>
        {has_converted && cmp?.validation_status && <StatusBadge status={cmp.validation_status} />}
      </Box>

      {!has_converted && (
        <Alert severity="info" sx={{ mb: 2 }}>
          The converted codebase dependency graph will appear here after transformation completes.
        </Alert>
      )}

      {/* Combined score banner */}
      {has_converted && cmp && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2.5, bgcolor: bannerBg, borderColor: bannerBorder }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
            <Box>
              <Typography variant="subtitle1" fontWeight={700}>
                Overall Structural Similarity: {cmp.combined_score?.toFixed(1) ?? '—'}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {cmp.nodes_matched} of {origM.file_nodes ?? 0} files matched
                {' · '}{cmp.classes_matched ?? 0} classes preserved
                {' · '}{cmp.edges_preserved} relations kept
                {cmp.cycles_resolved > 0 && ` · ${cmp.cycles_resolved} cycle${cmp.cycles_resolved > 1 ? 's' : ''} resolved`}
              </Typography>
            </Box>
            <Typography
              variant="h4"
              fontWeight={800}
              sx={{ color: cmp.validation_status === 'pass' ? 'success.main' : cmp.validation_status === 'warn' ? 'warning.main' : 'error.main' }}
            >
              {cmp.combined_score?.toFixed(0) ?? '—'}%
            </Typography>
          </Box>
        </Paper>
      )}

      {/* Side-by-side graphs */}
      <Grid container spacing={2} alignItems="center" sx={{ mb: 2.5 }}>
        {/* Initial */}
        <Grid item xs={12} md={5}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>Initial Codebase</Typography>
            <GraphCanvas graph={initial_graph} label={origLabel} emptyMessage="No graph data yet" />
            <Legend />
            <GraphChips m={origM} />
          </Paper>
        </Grid>

        {/* Center connector — always rendered, state-aware */}
        <Grid item xs={12} md={2} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          {!has_converted ? (
            // Transformation not done yet
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.75 }}>
              <SwapIcon sx={{ fontSize: 32, color: 'text.disabled' }} />
              <Typography variant="caption" color="text.disabled" textAlign="center">
                Awaiting transformation
              </Typography>
            </Box>
          ) : !cmp ? (
            // Has converted graph but no comparison yet
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.75 }}>
              <CircularProgress size={28} thickness={4} />
              <Typography variant="caption" color="text.secondary" textAlign="center">
                Computing…
              </Typography>
            </Box>
          ) : (() => {
            // Use combined_score (same as the banner) for the center ring
            const score = cmp.combined_score ?? 0;
            const structScore = cmp.structure_match_score ?? 0;
            const scoreColor =
              score >= 70 ? '#4caf50' :
              score >= 45 ? '#ff9800' :
              '#f44336';
            const scoreLabel =
              score >= 70 ? 'Strong match' :
              score >= 45 ? 'Partial match' :
              'Low match';
            return (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                {/* Circular score ring — Overall Structural Similarity */}
                <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                  {/* Background track */}
                  <CircularProgress
                    variant="determinate"
                    value={100}
                    size={72}
                    thickness={5}
                    sx={{ color: '#e0e0e0', position: 'absolute', left: 0, top: 0 }}
                  />
                  {/* Foreground score */}
                  <CircularProgress
                    variant="determinate"
                    value={Math.min(score, 100)}
                    size={72}
                    thickness={5}
                    sx={{ color: scoreColor }}
                  />
                  <Box sx={{
                    position: 'absolute', inset: 0,
                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Typography variant="caption" fontWeight={800} sx={{ color: scoreColor, fontSize: '0.82rem', lineHeight: 1 }}>
                      {score.toFixed(1)}%
                    </Typography>
                  </Box>
                </Box>
                {/* Swap arrows */}
                <SwapIcon sx={{ fontSize: 20, color: scoreColor }} />
                {/* "Overall Structural Similarity" label */}
                <Typography variant="caption" fontWeight={700} sx={{ color: scoreColor, textAlign: 'center', lineHeight: 1.3, fontSize: '0.7rem' }}>
                  Overall Structural<br />Similarity
                </Typography>
                {/* Sub-label */}
                <Typography variant="caption" sx={{ color: 'text.secondary', textAlign: 'center', fontSize: '0.65rem' }}>
                  {scoreLabel} · {structScore.toFixed(0)}% files
                </Typography>
                {/* Cycles resolved badge */}
                {cmp.cycles_resolved > 0 && (
                  <Chip
                    label={`${cmp.cycles_resolved} cycle${cmp.cycles_resolved > 1 ? 's' : ''} fixed`}
                    size="small"
                    color="success"
                    sx={{ fontSize: '0.65rem', height: 18 }}
                  />
                )}
              </Box>
            );
          })()}
        </Grid>

        {/* Converted — always rendered, placeholder when not yet available */}
        <Grid item xs={12} md={5}>
          <Paper variant="outlined" sx={{ p: 2, opacity: has_converted ? 1 : 0.45 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>Converted Codebase</Typography>
            <GraphCanvas
              graph={has_converted ? converted_graph : null}
              label={has_converted ? convLabel : '0 files · 0 imports'}
              emptyMessage={has_converted ? 'No converted graph data' : 'Available after transformation'}
            />
            <Legend />
            <GraphChips m={has_converted ? convM : {}} />
          </Paper>
        </Grid>
      </Grid>

      {/* Scores + metric diff */}
      {has_converted && cmp && (
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>Similarity Scores</Typography>
              <ScoreBar
                label="File Structure Match"
                value={cmp.structure_match_score}
                tip="% of original files whose logical name is present in the converted codebase"
              />
              <ScoreBar
                label="Class Preservation"
                value={cmp.class_match_score ?? 0}
                tip="% of original classes whose logical name is present in the converted codebase"
              />
              <ScoreBar
                label="Relation Preservation"
                value={cmp.edge_preservation_rate}
                tip="% of original import relations preserved in the converted graph"
              />
              <Divider sx={{ my: 1 }} />
              <ScoreBar
                label="Combined Structural Score"
                value={cmp.combined_score ?? 0}
                tip="Weighted: 50% file match + 30% class match + 20% edge preservation"
              />
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.75 }}>
                <Typography variant="subtitle2" fontWeight={600}>Metric Diff</Typography>
                <Box sx={{ display: 'flex', gap: 1.5 }}>
                  {['Init', 'Conv', 'Δ'].map(h => (
                    <Typography key={h} variant="caption" color="text.secondary" sx={{ minWidth: 34, textAlign: 'right' }}>{h}</Typography>
                  ))}
                </Box>
              </Box>
              <Divider sx={{ mb: 0.5 }} />
              <MetricRow label="Total nodes" orig={origM.total_nodes ?? 0} conv={convM.total_nodes ?? 0} />
              <MetricRow label="File nodes" orig={origM.file_nodes ?? 0} conv={convM.file_nodes ?? 0} />
              <MetricRow label="Class nodes" orig={origM.class_nodes ?? 0} conv={convM.class_nodes ?? 0} />
              <MetricRow label="Function nodes" orig={origM.function_nodes ?? 0} conv={convM.function_nodes ?? 0} />
              <MetricRow label="Import edges" orig={origM.import_edges ?? 0} conv={convM.import_edges ?? 0} />
              <MetricRow label="Circular deps" orig={cmp.cycles_original} conv={cmp.cycles_converted} />
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Relation mapping */}
      {has_converted && cmp && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>Relation Mapping</Typography>
          <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
            <Tooltip title="Import relations present in both graphs (by logical name)">
              <Chip label={`${cmp.edges_preserved} preserved`} color="success" size="small" />
            </Tooltip>
            <Tooltip title="Import relations from original not found in converted">
              <Chip label={`${cmp.edges_removed} removed`} color={cmp.edges_removed > 0 ? 'warning' : 'default'} size="small" />
            </Tooltip>
            <Tooltip title="New import relations introduced in converted codebase">
              <Chip label={`${cmp.edges_added} added`} color="info" size="small" />
            </Tooltip>
            {cmp.cycles_resolved > 0 && (
              <Tooltip title="Circular dependencies eliminated during conversion">
                <Chip label={`${cmp.cycles_resolved} cycle${cmp.cycles_resolved > 1 ? 's' : ''} resolved`} color="success" size="small" />
              </Tooltip>
            )}
          </Box>
        </Paper>
      )}

      {/* File diff lists */}
      {has_converted && cmp && (cmp.nodes_only_in_original.length > 0 || cmp.nodes_only_in_converted.length > 0) && (
        <Grid container spacing={2}>
          {cmp.nodes_only_in_original.length > 0 && (
            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" color="warning.main" gutterBottom>
                  Only in initial ({cmp.nodes_only_in_original.length})
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {cmp.nodes_only_in_original.slice(0, 15).map(n => (
                    <Chip key={n} label={n} size="small" variant="outlined" sx={{ fontSize: 10 }} />
                  ))}
                  {cmp.nodes_only_in_original.length > 15 && (
                    <Chip label={`+${cmp.nodes_only_in_original.length - 15} more`} size="small" />
                  )}
                </Box>
              </Paper>
            </Grid>
          )}
          {cmp.nodes_only_in_converted.length > 0 && (
            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" color="info.main" gutterBottom>
                  New in converted ({cmp.nodes_only_in_converted.length})
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {cmp.nodes_only_in_converted.slice(0, 15).map(n => (
                    <Chip key={n} label={n} size="small" variant="outlined" color="info" sx={{ fontSize: 10 }} />
                  ))}
                  {cmp.nodes_only_in_converted.length > 15 && (
                    <Chip label={`+${cmp.nodes_only_in_converted.length - 15} more`} size="small" color="info" />
                  )}
                </Box>
              </Paper>
            </Grid>
          )}
        </Grid>
      )}
    </Box>
  );
}
