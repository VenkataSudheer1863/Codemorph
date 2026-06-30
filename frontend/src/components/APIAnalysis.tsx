import React, { useState, useEffect, useRef } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Button, Alert, CircularProgress,
  Grid, Tooltip,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { api, type APIAnalysis } from '../api';

interface APIAnalysisProps { projectId: string; }

const METHOD_COLORS: Record<string, 'success' | 'primary' | 'warning' | 'error' | 'info' | 'default'> = {
  GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'error', PATCH: 'info',
};

export const APIAnalysisComponent: React.FC<APIAnalysisProps> = ({ projectId }) => {
  const [analysis, setAnalysis] = useState<APIAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectStatus, setProjectStatus] = useState<string>('');
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollCount = useRef(0);

  const fetchProjectStatus = async () => {
    try {
      const res = await fetch(`/api/projects/${projectId}`);
      if (res.ok) { const p = await res.json(); setProjectStatus(p.status); }
    } catch (e) { console.error('Failed to fetch project status:', e); }
  };

  const fetchResults = async (): Promise<APIAnalysis | null> => {
    try {
      const result = await api.getAPIAnalysis(projectId);
      setAnalysis(result);
      return result;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch API analysis');
      return null;
    }
  };

  // Trigger analysis on the backend then poll until endpoints appear
  const triggerAndPoll = async () => {
    setLoading(true);
    setError(null);
    pollCount.current = 0;

    try {
      await api.startAPIAnalysis(projectId);
    } catch {
      // startAPIAnalysis may fail if already running — continue polling anyway
    }

    const poll = async () => {
      pollCount.current += 1;
      const result = await fetchResults();
      const hasEndpoints = (result?.statistics?.total_endpoints ?? 0) > 0;

      if (!hasEndpoints && pollCount.current < 12) {
        pollRef.current = setTimeout(poll, 2000);
      } else {
        setLoading(false);
      }
    };

    pollRef.current = setTimeout(poll, 1500);
  };

  // On mount / projectId change: fetch existing results first.
  // If none found, auto-trigger analysis so converted endpoints appear.
  const initialLoad = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getAPIAnalysis(projectId);
      setAnalysis(result);
      if ((result?.statistics?.total_endpoints ?? 0) === 0) {
        // No endpoints yet — kick off analysis automatically
        await triggerAndPoll();
        return;
      }
    } catch {
      // No existing result — trigger fresh analysis
      await triggerAndPoll();
      return;
    }
    setLoading(false);
  };

  useEffect(() => { fetchProjectStatus(); }, [projectId]);

  useEffect(() => {
    if (projectStatus === 'complete') initialLoad();
    return () => { if (pollRef.current) clearTimeout(pollRef.current); };
  }, [projectStatus]);

  if (projectStatus !== 'complete') {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">
          API analysis is only available after transformation completion.
        </Alert>
      </Box>
    );
  }

  if (loading && !analysis) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="400px" gap={2}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary">
          Analysing converted codebase for API endpoints…
        </Typography>
      </Box>
    );
  }

  if (error && !analysis) {
    return <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>;
  }

  if (!analysis) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info" sx={{ mb: 2 }}>No API analysis data available.</Alert>
        <Button variant="contained" onClick={triggerAndPoll} disabled={loading}>
          {loading ? 'Analysing…' : 'Run API Analysis'}
        </Button>
      </Box>
    );
  }

  const endpoints = analysis.endpoints ?? [];
  const stats = analysis.statistics;

  return (
    <Box>
      {/* Stats row */}
      <Grid container spacing={2} mb={3}>
        {[
          { label: 'API Endpoints',  value: stats.total_endpoints,              color: 'primary.main' },
          { label: 'Unique Paths',   value: stats.unique_paths,                 color: 'info.main' },
          { label: 'Frameworks',     value: (analysis.frameworks ?? []).length, color: 'warning.main' },
        ].map(({ label, value, color }) => (
          <Grid item xs={6} sm={3} key={label}>
            <Card>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="h4" fontWeight="bold" sx={{ color }}>{value}</Typography>
                <Typography variant="body2" color="text.secondary">{label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Endpoints table */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight={600}>
              API Endpoints ({endpoints.length})
            </Typography>
            <Button
              size="small"
              startIcon={loading ? <CircularProgress size={14} /> : <RefreshIcon />}
              onClick={triggerAndPoll}
              disabled={loading}
            >
              {loading ? 'Analysing…' : 'Refresh'}
            </Button>
          </Box>

          {endpoints.length === 0 ? (
            <Alert severity="info">
              No API endpoints found in the converted codebase.
            </Alert>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Method</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Path</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Function</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>File</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {endpoints.map((ep, i) => (
                    <TableRow key={i} hover>
                      <TableCell>
                        <Chip
                          label={ep.method}
                          color={METHOD_COLORS[ep.method.toUpperCase()] ?? 'default'}
                          size="small"
                          sx={{ fontWeight: 700, minWidth: 60 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace" color="primary.main">
                          {ep.path}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {ep.function_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={ep.file_path || ''}>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                          >
                            {ep.file_path ? ep.file_path.split('/').slice(-2).join('/') : '—'}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default APIAnalysisComponent;
