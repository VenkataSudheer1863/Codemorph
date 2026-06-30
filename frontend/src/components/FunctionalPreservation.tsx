import { useEffect, useState } from 'react';
import {
  Box, Typography, Card, CardContent, Chip, Alert, CircularProgress,
  LinearProgress, Grid, Divider, Accordion, AccordionSummary, AccordionDetails,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tooltip,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Warning as WarnIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  Shield as ShieldIcon,
} from '@mui/icons-material';
import { api, type FunctionalPreservationReport } from '../api';

interface Props { projectId: string; }

function ScoreRing({ score, size = 72 }: { score: number; size?: number }) {
  const color = score >= 0.8 ? '#4caf50' : score >= 0.6 ? '#ff9800' : '#f44336';
  return (
    <Box sx={{ position: 'relative', display: 'inline-flex' }}>
      <CircularProgress variant="determinate" value={100} size={size} thickness={5}
        sx={{ color: '#e0e0e0', position: 'absolute', left: 0, top: 0 }} />
      <CircularProgress variant="determinate" value={Math.min(score * 100, 100)} size={size} thickness={5}
        sx={{ color }} />
      <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="caption" fontWeight={800} sx={{ color, fontSize: '0.85rem' }}>
          {(score * 100).toFixed(0)}%
        </Typography>
      </Box>
    </Box>
  );
}

function VerdictChip({ verdict }: { verdict: string }) {
  if (verdict === 'preserved') return <Chip icon={<CheckIcon />} label="Preserved" color="success" size="small" />;
  if (verdict === 'partial') return <Chip icon={<WarnIcon />} label="Partial" color="warning" size="small" />;
  return <Chip icon={<ErrorIcon />} label="Logic Lost" color="error" size="small" />;
}

export default function FunctionalPreservationComponent({ projectId }: Props) {
  const [data, setData] = useState<FunctionalPreservationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.getFunctionalPreservation(projectId)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <Box display="flex" justifyContent="center" py={5}><CircularProgress size={36} /></Box>;
  if (error) return <Alert severity="error">{error}</Alert>;
  if (!data) return null;

  if (!data.available) {
    return (
      <Alert severity="info" icon={<ShieldIcon />}>
        {data.message || 'Functional preservation report will be available after transformation completes.'}
      </Alert>
    );
  }

  const score = data.overall_score ?? 0;
  const scoreColor = score >= 0.8 ? 'success.main' : score >= 0.6 ? 'warning.main' : 'error.main';
  const apiRate = (data.api_preservation_rate ?? 0) / 100;
  const apiColor = apiRate >= 0.9 ? '#4caf50' : apiRate >= 0.7 ? '#ff9800' : '#f44336';

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={1.5} mb={2}>
        <ShieldIcon color="primary" />
        <Typography variant="h6">Functional Preservation Report</Typography>
        {data.overall_passed
          ? <Chip icon={<CheckIcon />} label="Logic Preserved" color="success" size="small" />
          : <Chip icon={<WarnIcon />} label="Review Required" color="warning" size="small" />}
      </Box>

      {/* Score banner */}
      <Card sx={{
        mb: 3, p: 2,
        bgcolor: score >= 0.8 ? '#e8f5e9' : score >= 0.6 ? '#fff8e1' : '#ffebee',
        border: '1px solid',
        borderColor: score >= 0.8 ? 'success.light' : score >= 0.6 ? 'warning.light' : 'error.light',
      }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={2}>
          <Box display="flex" alignItems="center" gap={3}>
            <ScoreRing score={score} size={80} />
            <Box>
              <Typography variant="h6" fontWeight={700} sx={{ color: scoreColor }}>
                Overall Preservation Score
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {data.files_passed}/{data.files_checked} files passed ·{' '}
                {data.api_preservation_rate?.toFixed(1)}% API contracts preserved
              </Typography>
            </Box>
          </Box>
          <Box display="flex" gap={2} flexWrap="wrap">
            <Box textAlign="center">
              <Typography variant="h5" fontWeight={800} sx={{ color: scoreColor }}>
                {data.preservation_rate?.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">Logic Preserved</Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h5" fontWeight={800} sx={{ color: apiColor }}>
                {data.api_preservation_rate?.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">API Contracts</Typography>
            </Box>
          </Box>
        </Box>
      </Card>

      <Grid container spacing={2} mb={3}>
        {/* API Contract Check */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>API Contract Verification</Typography>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">Endpoints preserved</Typography>
                <Typography variant="body2" fontWeight={700} sx={{ color: apiColor }}>
                  {data.api_contract_check?.preserved_endpoints}/{data.api_contract_check?.total_endpoints}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min((data.api_contract_check?.preservation_rate ?? 0) * 100, 100)}
                sx={{ height: 7, borderRadius: 4, bgcolor: '#e0e0e0', mb: 1.5,
                  '& .MuiLinearProgress-bar': { bgcolor: apiColor, borderRadius: 4 } }}
              />
              {(data.api_contract_check?.missing_endpoints?.length ?? 0) > 0 && (
                <>
                  <Typography variant="caption" color="error.main" fontWeight={600}>
                    Missing endpoints:
                  </Typography>
                  {data.api_contract_check!.missing_endpoints.slice(0, 5).map((ep, i) => (
                    <Box key={i} display="flex" gap={1} mt={0.5}>
                      <Chip label={ep.method} size="small" color="error" variant="outlined" sx={{ fontSize: '0.65rem', height: 18 }} />
                      <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'error.main' }}>{ep.path}</Typography>
                    </Box>
                  ))}
                </>
              )}
              {(data.api_contract_check?.missing_endpoints?.length ?? 0) === 0 && (
                <Chip icon={<CheckIcon />} label="All endpoints preserved" color="success" size="small" />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* File Summary */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>File-Level Summary</Typography>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">Files checked</Typography>
                <Typography variant="body2" fontWeight={700}>{data.files_checked}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">Fully preserved</Typography>
                <Typography variant="body2" fontWeight={700} color="success.main">{data.files_passed}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">Need review</Typography>
                <Typography variant="body2" fontWeight={700} color="warning.main">{data.files_failed}</Typography>
              </Box>
              <Divider sx={{ my: 1 }} />
              <LinearProgress
                variant="determinate"
                value={data.files_checked ? ((data.files_passed ?? 0) / data.files_checked) * 100 : 0}
                sx={{ height: 7, borderRadius: 4, bgcolor: '#e0e0e0',
                  '& .MuiLinearProgress-bar': { bgcolor: '#4caf50', borderRadius: 4 } }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Failed files detail */}
      {(data.failed_files_summary?.length ?? 0) > 0 && (
        <>
          <Typography variant="subtitle1" fontWeight={600} mb={1} color="warning.main">
            Files Requiring Review ({data.failed_files_summary!.length})
          </Typography>
          {data.failed_files_summary!.map((f, i) => (
            <Accordion key={i} sx={{ mb: 0.5 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" gap={2} flex={1}>
                  <VerdictChip verdict={f.verdict} />
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>
                    {f.file.split('/').pop() || f.file}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto', mr: 1 }}>
                    {f.summary}
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', display: 'block', mb: 1 }}>
                  {f.file}
                </Typography>
                {f.missing.length > 0 && (
                  <Box>
                    <Typography variant="caption" color="error.main" fontWeight={600}>Missing logic:</Typography>
                    {f.missing.map((m, j) => (
                      <Typography key={j} variant="caption" display="block" sx={{ ml: 1, color: 'error.main' }}>• {m}</Typography>
                    ))}
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          ))}
        </>
      )}

      {/* All file results table */}
      {(data.file_results?.length ?? 0) > 0 && (
        <Box mt={3}>
          <Typography variant="subtitle1" fontWeight={600} mb={1}>All Files</Typography>
          <Card variant="outlined">
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>File</TableCell>
                    <TableCell>Verdict</TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>Method</TableCell>
                    <TableCell>Summary</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.file_results!.slice(0, 30).map((r, i) => (
                    <TableRow key={i} hover>
                      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.78rem', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        <Tooltip title={r.file_path}>
                          <span>{r.file_path.split('/').pop() || r.file_path}</span>
                        </Tooltip>
                      </TableCell>
                      <TableCell><VerdictChip verdict={r.verdict} /></TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight={700}
                          sx={{ color: r.score >= 0.8 ? 'success.main' : r.score >= 0.6 ? 'warning.main' : 'error.main' }}>
                          {(r.score * 100).toFixed(0)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={r.verification_method} size="small" variant="outlined" sx={{ fontSize: '0.65rem' }} />
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.78rem', color: 'text.secondary', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        <Tooltip title={r.summary}><span>{r.summary}</span></Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Card>
        </Box>
      )}
    </Box>
  );
}
