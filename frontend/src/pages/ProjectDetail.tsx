import { useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Button,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  IconButton,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Radio,
  RadioGroup,
  FormControlLabel,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Tooltip,
  InputAdornment,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  PlayArrow as PlayIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  CheckCircle as CheckIcon,
  RadioButtonUnchecked as CircleIcon,
  Pending as PendingIcon,
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Storage as StorageIcon,
  Api as ApiIcon,
  Assessment as AssessmentIcon,
  Edit as EditIcon,
  Check as SaveIcon,
  Close as CancelIcon,
  Shield as ShieldIcon,
} from '@mui/icons-material';
import { api, type Project } from '../api';
import StatusBadge from '../components/StatusBadge';
import { DatabaseAnalysisComponent } from '../components/DatabaseAnalysis';
import { APIAnalysisComponent } from '../components/APIAnalysis';
import { ValidationDashboardComponent } from '../components/ValidationDashboard';
import FunctionalPreservationComponent from '../components/FunctionalPreservation';
import StatCard from '../components/StatCard';
import ProgressBar from '../components/ProgressBar';
import { useToast } from '../components/ToastProvider';

const PIPELINE_STAGES = [
  'created',
  'ingesting',
  'parsing',
  'context_building',
  'agentic_analysis',
  'selecting',
  'transforming',
  'post_transformation_analysis',
  'complete',
];

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState(0);
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [customInputs, setCustomInputs] = useState<Record<string, string>>({});
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState('');

  // Determine active tab from URL
  const tabFromUrl = location.pathname.split('/').pop();
  const tabMap: Record<string, number> = {
    overview: 0,
    'context-built': 1,
    stack: 2,
    'select-stack': 3,
    transformation: 4,
    'database-analysis': 5,
    'api-analysis': 6,
    validation: 7,
    'functional-preservation': 8,
  };

  // Sync tab with URL
  if (tabFromUrl && tabMap[tabFromUrl] !== undefined && activeTab !== tabMap[tabFromUrl]) {
    setActiveTab(tabMap[tabFromUrl]);
  }

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => api.getProject(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      const running = !['created', 'complete', 'error', 'cancelled', 'selecting'].includes(data.status);
      return running ? 2000 : false;
    },
  });

  const startMutation = useMutation({
    mutationFn: () => api.startPipeline(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      showToast('Pipeline started successfully!', 'success');
    },
    onError: (error: Error) => {
      showToast(`Failed to start pipeline: ${error.message}`, 'error');
    },
  });

  const selectStackMutation = useMutation({
    mutationFn: () => api.selectStack(id!, selections),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      showToast('Stack selection saved! Transformation started.', 'success');
    },
    onError: (error: Error) => {
      showToast(`Failed to save stack selection: ${error.message}`, 'error');
    },
  });

  const renameMutation = useMutation({
    mutationFn: (name: string) => api.updateProject(id!, { name }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['project', id], updated);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setEditingName(false);
      showToast('Project renamed successfully!', 'success');
    },
    onError: (error: Error) => {
      showToast(`Failed to rename project: ${error.message}`, 'error');
    },
  });

  // Initialize selections from recommendations
  if (project?.recommendations && Object.keys(selections).length === 0 && project.recommendations.length > 0) {
    const init: Record<string, string> = {};
    for (const rec of project.recommendations) {
      if (rec.suggestions && rec.suggestions.length > 0) {
        init[rec.category] = rec.suggestions[0];
      }
    }
    setSelections(init);
  }

  if (isLoading || !project) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  const currentStageIdx = PIPELINE_STAGES.indexOf(project.status);

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <IconButton onClick={() => navigate('/')} size="small">
          <ArrowBackIcon />
        </IconButton>
        <Box flex={1}>
          {editingName ? (
            <Box display="flex" alignItems="center" gap={1}>
              <TextField
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && nameInput.trim()) renameMutation.mutate(nameInput.trim());
                  if (e.key === 'Escape') setEditingName(false);
                }}
                size="small"
                autoFocus
                disabled={renameMutation.isPending}
                sx={{ minWidth: 260 }}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <Tooltip title="Save (Enter)">
                        <span>
                          <IconButton
                            size="small"
                            onClick={() => nameInput.trim() && renameMutation.mutate(nameInput.trim())}
                            disabled={!nameInput.trim() || renameMutation.isPending}
                            color="primary"
                          >
                            <SaveIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                      <Tooltip title="Cancel (Esc)">
                        <IconButton size="small" onClick={() => setEditingName(false)}>
                          <CancelIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
          ) : (
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="h5" fontWeight={700}>
                {project.name}
              </Typography>
              <Tooltip title="Rename project">
                <IconButton
                  size="small"
                  onClick={() => { setNameInput(project.name); setEditingName(true); }}
                  sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
                >
                  <EditIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          )}
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
          >
            {project.path}
          </Typography>
        </Box>
        <StatusBadge status={project.status} />
        {project.status === 'created' && (
          <Button
            variant="contained"
            startIcon={<PlayIcon />}
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
          >
            {startMutation.isPending ? 'Starting...' : 'Start Analysis'}
          </Button>
        )}
        {(project.status === 'error' || project.status === 'cancelled') && (
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
          >
            Restart Pipeline
          </Button>
        )}
      </Box>

      {project.status === 'error' && project.error_message && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {project.error_message}
        </Alert>
      )}

      {/* Pipeline Stepper */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stepper activeStep={currentStageIdx} alternativeLabel>
            {PIPELINE_STAGES.map((stage, idx) => {
              const isDone = idx < currentStageIdx || (stage === 'complete' && project.status === 'complete');
              const isActive = idx === currentStageIdx && stage !== 'complete';
              return (
                <Step key={stage} completed={isDone}>
                  <StepLabel
                    StepIconComponent={() => {
                      if (isDone) return <CheckIcon color="success" />;
                      if (isActive) return <PendingIcon color="primary" />;
                      return <CircleIcon color="disabled" />;
                    }}
                  >
                    {stage === 'context_building' ? 'Agentic Analysis' : stage === 'agentic_analysis' ? 'Context Building' : stage.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </StepLabel>
                </Step>
              );
            })}
          </Stepper>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Card sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => {
            setActiveTab(v);
            const tabNames = ['overview', 'context-built', 'stack', 'select-stack', 'transformation', 'database-analysis', 'api-analysis', 'validation', 'functional-preservation'];
            navigate(`/project/${id}/${tabNames[v]}`, { replace: true });
          }}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Overview" />
          <Tab 
            label="Context Built" 
            disabled={
              PIPELINE_STAGES.indexOf(project.status) < PIPELINE_STAGES.indexOf('context_building') ||
              !project.architecture_layers || 
              Object.keys(project.architecture_layers || {}).length === 0
            } 
          />
          <Tab 
            label="Tech Stack" 
            disabled={
              PIPELINE_STAGES.indexOf(project.status) < PIPELINE_STAGES.indexOf('selecting') ||
              !project.detected_stack || 
              project.detected_stack.length === 0
            } 
          />
          <Tab 
            label="Select Stack" 
            disabled={
              PIPELINE_STAGES.indexOf(project.status) < PIPELINE_STAGES.indexOf('selecting') ||
              !project.recommendations || 
              project.recommendations.length === 0
            } 
          />
          <Tab 
            label="Transformation" 
            disabled={
              PIPELINE_STAGES.indexOf(project.status) < PIPELINE_STAGES.indexOf('transforming') ||
              (!project.transformation_mappings || project.transformation_mappings.length === 0)
            } 
          />
          <Tab 
            label="Database Analysis" 
            icon={<StorageIcon />}
            disabled={
              PIPELINE_STAGES.indexOf(project.status) < PIPELINE_STAGES.indexOf('complete')
            }
          />
          <Tab 
            label="API Analysis" 
            icon={<ApiIcon />}
            disabled={
              PIPELINE_STAGES.indexOf(project.status) < PIPELINE_STAGES.indexOf('complete')
            }
          />
          <Tab 
            label="Validation" 
            icon={<AssessmentIcon />}
            disabled={
              PIPELINE_STAGES.indexOf(project.status) < PIPELINE_STAGES.indexOf('complete')
            }
          />
          <Tab
            label="Functional Preservation"
            icon={<ShieldIcon />}
            disabled={
              PIPELINE_STAGES.indexOf(project.status) < PIPELINE_STAGES.indexOf('complete')
            }
          />
        </Tabs>
      </Card>

      {/* Tab Content */}
      {activeTab === 0 && <OverviewTab project={project} />}
      {activeTab === 1 && <ContextBuiltTab project={project} />}
      {activeTab === 2 && <StackTab project={project} />}
      {activeTab === 3 && (
        <SelectStackTab
          project={project}
          selections={selections}
          setSelections={setSelections}
          customInputs={customInputs}
          setCustomInputs={setCustomInputs}
          onSubmit={() => selectStackMutation.mutate()}
          isPending={selectStackMutation.isPending}
        />
      )}
      {activeTab === 4 && <TransformationTab project={project} />}
      {activeTab === 5 && <DatabaseAnalysisComponent projectId={project.id} />}
      {activeTab === 6 && <APIAnalysisComponent projectId={project.id} />}
      {activeTab === 7 && <ValidationDashboardComponent projectId={project.id} />}
      {activeTab === 8 && <FunctionalPreservationComponent projectId={project.id} />}
    </Box>
  );
}

// Tab Components
function OverviewTab({ project }: { project: Project }) {
  const langDist = project.language_distribution || {};
  const langs = Object.entries(langDist).sort((a, b) => b[1] - a[1]);

  return (
    <Box>
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Total Files" value={project.total_files || 0} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Lines of Code" value={project.total_loc || 0} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Languages" value={project.languages_count || 0} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Frameworks" value={project.frameworks_count || 0} />
        </Grid>
      </Grid>

      {langs.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={600} mb={3}>
              Language Distribution
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              {langs.map(([lang, pct]) => (
                <Box key={lang}>
                  <Box display="flex" justifyContent="space-between" mb={0.5}>
                    <Chip label={lang} size="small" />
                    <Typography variant="body2" color="text.secondary" fontWeight={600}>
                      {pct}%
                    </Typography>
                  </Box>
                  <ProgressBar value={pct} showPercent={false} />
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

function ContextBuiltTab({ project }: { project: Project }) {
  const layers = project.architecture_layers || {};
  const layerOrder = ['frontend', 'backend', 'database', 'integration', 'deployment'];
  const apis = project.detected_apis || [];
  const tables = project.detected_tables || [];
  const detectedStack = project.detected_stack || [];
  const summary = project.project_summary || '';

  // Filter out empty layers (no files)
  const populatedLayers = layerOrder.filter((layer) => {
    const data = layers[layer];
    return data && data.file_count > 0;
  });

  const methodColors: Record<string, 'success' | 'primary' | 'warning' | 'error' | 'secondary'> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'error',
    PATCH: 'secondary',
  };

  // Check if context building is complete
  const contextBuildingComplete = PIPELINE_STAGES.indexOf(project.status) >= PIPELINE_STAGES.indexOf('selecting');

  if (!contextBuildingComplete) {
    return (
      <Alert severity="info">
        Context building is in progress. This tab will be available once the context building stage completes.
      </Alert>
    );
  }

  if (populatedLayers.length === 0 && apis.length === 0 && tables.length === 0 && detectedStack.length === 0) {
    return (
      <Alert severity="warning">
        No architecture context was built for this project. The codebase may not contain recognizable patterns.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Codebase Documentation — LLM-generated, shown first and prominently */}
      {summary && (
        <Card sx={{ mb: 4, border: '1px solid', borderColor: 'divider' }}>
          <CardContent>
            <Typography variant="h6" fontWeight={600} mb={2}>
              Codebase Documentation
            </Typography>
            <Box>
              {summary.split('\n').filter(p => p.trim()).map((paragraph, i) => (
                <Typography
                  key={i}
                  variant="body1"
                  sx={{ lineHeight: 1.8, mb: 1.5, color: 'text.primary' }}
                >
                  {paragraph}
                </Typography>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Detected Technology Stack */}
      {detectedStack.length > 0 && (
        <>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Detected Technology Stack
          </Typography>
          <Grid container spacing={2} mb={4}>
            {detectedStack.map((tech, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {tech.detected}
                      </Typography>
                      <Chip 
                        label={`${Math.round(tech.confidence)}%`} 
                        size="small" 
                        color={tech.confidence > 80 ? 'success' : tech.confidence > 60 ? 'warning' : 'default'}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" textTransform="capitalize" mb={1}>
                      {tech.category.replace('_', ' ')}
                    </Typography>
                    {tech.detected && tech.detected.includes('v') && (
                      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                        {tech.detected}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}

      {/* Architecture Layers - Only show populated layers */}
      {populatedLayers.length > 0 && (
        <>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Architecture Layers
          </Typography>
          <Grid container spacing={3} mb={4}>
            {populatedLayers.map((layer) => {
              const data = layers[layer];

              return (
                <Grid item xs={12} md={6} key={layer}>
                  <Card>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                        <Typography variant="h6" fontWeight={600} textTransform="capitalize">
                          {layer}
                        </Typography>
                        <Chip label={`${data.file_count || 0} files`} size="small" color="primary" />
                      </Box>
                      {data.frameworks && data.frameworks.length > 0 && (
                        <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                          {data.frameworks.map((fw: string) => (
                            <Chip key={fw} label={fw} size="small" color="primary" variant="outlined" />
                          ))}
                        </Box>
                      )}
                      {data.components && data.components.length > 0 && (
                        <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                          {data.components.slice(0, 8).join(', ')}
                          {data.components.length > 8 && ` +${data.components.length - 8} more`}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </>
      )}

      {/* API Endpoints */}
      {apis.length > 0 && (
        <>
          <Typography variant="h6" fontWeight={600} mb={2}>
            API Endpoints ({apis.length})
          </Typography>
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Method</TableCell>
                      <TableCell>Path</TableCell>
                      <TableCell>Handler</TableCell>
                      <TableCell>Type</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {apis.slice(0, 20).map((ep, i) => (
                      <TableRow key={i} hover>
                        <TableCell>
                          <Chip
                            label={ep.method}
                            size="small"
                            color={methodColors[ep.method] || 'default'}
                          />
                        </TableCell>
                        <TableCell sx={{ fontFamily: 'monospace', color: 'primary.main' }}>
                          {ep.path}
                        </TableCell>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                          {ep.handler}
                        </TableCell>
                        <TableCell>{ep.type}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              {apis.length > 20 && (
                <Typography variant="caption" color="text.secondary" mt={2} display="block">
                  Showing 20 of {apis.length} endpoints
                </Typography>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Database Objects */}
      {tables.length > 0 && (
        <>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Database Objects ({tables.length})
          </Typography>
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Columns</TableCell>
                      <TableCell>Relationships</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tables.slice(0, 20).map((tbl, i) => (
                      <TableRow key={i} hover>
                        <TableCell sx={{ fontFamily: 'monospace', color: 'primary.main' }}>
                          {tbl.name}
                        </TableCell>
                        <TableCell>
                          <Chip label={tbl.type} size="small" color="secondary" variant="outlined" />
                        </TableCell>
                        <TableCell>{tbl.columns}</TableCell>
                        <TableCell>{tbl.relationships}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              {tables.length > 20 && (
                <Typography variant="caption" color="text.secondary" mt={2} display="block">
                  Showing 20 of {tables.length} database objects
                </Typography>
              )}
            </CardContent>
          </Card>
        </>
      )}

    </Box>
  );
}

function StackTab({ project }: { project: Project }) {
  const stack = project.detected_stack || [];

  return (
    <Grid container spacing={3}>
      {stack.map((item, i) => (
        <Grid item xs={12} sm={6} md={4} key={i}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary" textTransform="uppercase" fontWeight={700}>
                {item.label}
              </Typography>
              <Typography variant="h6" fontWeight={600} my={1}>
                {item.detected}
              </Typography>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2" color="text.secondary">
                  Confidence
                </Typography>
                <Typography variant="body2" color="primary.main" fontWeight={600}>
                  {item.confidence}%
                </Typography>
              </Box>
              <ProgressBar value={item.confidence} showPercent={false} />
              {item.alternatives && item.alternatives.length > 0 && (
                <Box display="flex" flexWrap="wrap" gap={0.5} mt={2}>
                  {item.alternatives.map((alt) => (
                    <Chip key={alt} label={alt} size="small" variant="outlined" />
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}

interface SelectStackTabProps {
  project: Project;
  selections: Record<string, string>;
  setSelections: (s: Record<string, string>) => void;
  customInputs: Record<string, string>;
  setCustomInputs: (s: Record<string, string>) => void;
  onSubmit: () => void;
  isPending: boolean;
}

function SelectStackTab({ project, selections, setSelections, customInputs, setCustomInputs, onSubmit, isPending }: SelectStackTabProps) {
  const recommendations = project.recommendations || [];

  if (project.status !== 'selecting') {
    return (
      <Alert severity="info">
        {PIPELINE_STAGES.indexOf(project.status) < PIPELINE_STAGES.indexOf('selecting')
          ? 'Stack selection will be available after recommendations are generated.'
          : 'Stack has been selected. See Transformation tab for progress.'}
      </Alert>
    );
  }

  const handleCustomInput = (category: string, value: string) => {
    setCustomInputs({ ...customInputs, [category]: value });
    setSelections({ ...selections, [category]: value });
  };

  return (
    <Box>
      <Typography variant="h6" fontWeight={600} mb={1}>
        Select Target Stack
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Choose the modern technologies for each component of your application. You can select from recommendations or enter a custom technology.
      </Typography>

      <Grid container spacing={3} mb={3}>
        {recommendations.map((rec) => (
          <Grid item xs={12} md={6} key={rec.category}>
            <Card>
              <CardContent>
                <Typography variant="caption" color="text.secondary" textTransform="uppercase" fontWeight={700}>
                  {rec.label}
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={1} mb={2}>
                  Current: <strong style={{ color: '#f59e0b' }}>{rec.detected}</strong> ({rec.confidence}%)
                </Typography>
                <RadioGroup
                  value={selections[rec.category] || ''}
                  onChange={(e) => {
                    setSelections({ ...selections, [rec.category]: e.target.value });
                    setCustomInputs({ ...customInputs, [rec.category]: '' });
                  }}
                >
                  {rec.suggestions.map((suggestion) => (
                    <FormControlLabel
                      key={suggestion}
                      value={suggestion}
                      control={<Radio />}
                      label={suggestion}
                      sx={{
                        border: '1px solid',
                        borderColor: selections[rec.category] === suggestion ? 'primary.main' : 'divider',
                        borderRadius: 2,
                        mb: 1,
                        px: 1,
                        backgroundColor: selections[rec.category] === suggestion ? 'rgba(227,30,36,0.05)' : 'transparent',
                      }}
                    />
                  ))}
                </RadioGroup>
                
                <Divider sx={{ my: 2 }} />
                
                <Box display="flex" alignItems="center" gap={1}>
                  <AddIcon fontSize="small" color="primary" />
                  <Typography variant="body2" fontWeight={600} color="primary.main">
                    Or enter custom technology:
                  </Typography>
                </Box>
                <TextField
                  fullWidth
                  size="small"
                  placeholder={`e.g., Custom ${rec.label}`}
                  value={customInputs[rec.category] || ''}
                  onChange={(e) => handleCustomInput(rec.category, e.target.value)}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box display="flex" justifyContent="flex-end">
        <Button
          variant="contained"
          size="large"
          onClick={onSubmit}
          disabled={isPending || Object.keys(selections).length === 0}
        >
          {isPending ? 'Starting...' : 'Begin Transformation'}
        </Button>
      </Box>
    </Box>
  );
}

function TransformationTab({ project }: { project: Project }) {
  const mappings = project.transformation_mappings || [];
  const progress = project.transformation_progress || { processed: 0, total: 0, percent: 0 };
  const isComplete = project.status === 'complete';
  const isTransforming = project.status === 'transforming';
  const testScripts = project.test_scripts || [];

  return (
    <Box>
      {/* Progress */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight={600}>
              Transformation Progress
            </Typography>
            <Typography variant="h4" fontWeight={700} color="primary.main">
              {progress.percent > 0 ? Math.round(progress.percent) : 0}%
            </Typography>
          </Box>
          <LinearProgress variant="determinate" value={progress.percent || 0} sx={{ mb: 1, height: 8, '& .MuiLinearProgress-bar': { background: 'linear-gradient(90deg, #16a34a, #4ade80)' } }} />
          <Typography variant="body2" color="text.secondary">
            {progress.processed} / {progress.total} files processed
          </Typography>
          
          {/* Current File Display */}
          {isTransforming && progress.current_file && (
            <Box mt={2} p={2} sx={{ backgroundColor: 'rgba(227,30,36,0.05)', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary" mb={1}>
                Currently transforming:
              </Typography>
              <Typography 
                variant="body1" 
                fontWeight={500}
                sx={{ 
                  fontFamily: 'monospace', 
                  fontSize: '0.9rem',
                  color: 'primary.main',
                  wordBreak: 'break-all'
                }}
              >
                {progress.current_file}
              </Typography>
              {progress.current_mapping && (
                <Box display="flex" alignItems="center" gap={1} mt={1}>
                  <Typography variant="body2" color="text.secondary">
                    Converting to:
                  </Typography>
                  <Chip 
                    label={progress.current_mapping} 
                    size="small" 
                    color="primary" 
                    variant="outlined"
                  />
                </Box>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Mappings */}
      <Grid container spacing={2} mb={3}>
        {mappings.map((m, i) => (
          <Grid item xs={12} key={i}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2}>
                  {m.status === 'completed' ? (
                    <CheckIcon color="success" />
                  ) : m.status === 'active' ? (
                    <CircularProgress size={20} />
                  ) : (
                    <CircleIcon color="disabled" />
                  )}
                  <Box flex={1}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body2" color="warning.main" fontWeight={600}>
                        {m.source}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        →
                      </Typography>
                      <Typography variant="body2" color="primary.main" fontWeight={600}>
                        {m.target}
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {m.file_count} files
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Test Scripts */}
      {isComplete && testScripts.length > 0 && (
        <>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Generated Test Scripts
          </Typography>
          <Box mb={3}>
            {testScripts.map((script, i) => (
              <Accordion key={i}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center" gap={2} flex={1}>
                    <Chip label={script.type} color="primary" size="small" />
                    <Typography variant="body1" fontWeight={600}>
                      {script.file_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                      {script.framework}
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" color="text.secondary" mb={2}>
                    {script.description}
                  </Typography>
                  <Box
                    sx={{
                      backgroundColor: '#F5F5F7',
                      border: '1px solid #E5E5E7',
                      borderRadius: 2,
                      p: 2,
                      maxHeight: 400,
                      overflow: 'auto',
                    }}
                  >
                    <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>
                      {script.content}
                    </pre>
                  </Box>
                  <Box display="flex" justifyContent="flex-end" mt={2}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => {
                        const blob = new Blob([script.content], { type: 'text/plain' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = script.file_name;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                    >
                      Download
                    </Button>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        </>
      )}

      {/* Download */}
      {isComplete && (
        <Card sx={{ border: '1px solid', borderColor: 'primary.main', backgroundColor: 'rgba(227,30,36,0.05)' }}>
          <CardContent>
            <Typography variant="h6" fontWeight={600} color="primary.main" mb={1}>
              Transformation Complete!
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Download your modernized codebase, test scripts, and reports below.
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={2}>
              <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                href={api.downloadArtifacts(project.id)}
              >
                Modernized Codebase (ZIP)
              </Button>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                href={api.downloadLegacyReport(project.id)}
              >
                Legacy Analysis (PDF)
              </Button>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                href={api.downloadMigrationReport(project.id)}
              >
                Migration Report (PDF)
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
