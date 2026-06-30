import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  TableChart as TableChartIcon,
} from '@mui/icons-material';
import { api, type DatabaseAnalysis, type DatabaseTable } from '../api';

interface DatabaseAnalysisProps {
  projectId: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`database-tabpanel-${index}`}
      aria-labelledby={`database-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export const DatabaseAnalysisComponent: React.FC<DatabaseAnalysisProps> = ({ projectId }) => {
  const [analysis, setAnalysis] = useState<DatabaseAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTable, setSelectedTable] = useState<DatabaseTable | null>(null);
  const [ormDialogOpen, setOrmDialogOpen] = useState(false);
  const [selectedOrmModel, setSelectedOrmModel] = useState<string>('');
  const [tabValue, setTabValue] = useState(0);
  const [projectStatus, setProjectStatus] = useState<string>('');

  const fetchProjectStatus = async () => {
    try {
      const response = await fetch(`/api/projects/${projectId}`);
      if (response.ok) {
        const project = await response.json();
        setProjectStatus(project.status);
      }
    } catch (err) {
      console.error('Failed to fetch project status:', err);
    }
  };

  const fetchResults = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getDatabaseAnalysis(projectId);
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch database analysis');
    } finally {
      setLoading(false);
    }
  };

  const startAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.startDatabaseAnalysis(projectId);
      // Poll for results
      setTimeout(fetchResults, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start database analysis');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectStatus();
    if (projectStatus === 'complete') {
      fetchResults();
    }
  }, [projectId, projectStatus]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const openTableDetails = (table: DatabaseTable) => {
    setSelectedTable(table);
  };

  const openOrmModel = (_: string, modelContent: string) => {
    setSelectedOrmModel(modelContent);
    setOrmDialogOpen(true);
  };

  const downloadOrmModels = () => {
    if (!analysis?.orm_models) return;
    
    const modelsText = Object.entries(analysis.orm_models)
      .map(([name, code]) => `# ${name}\n${code}\n\n`)
      .join('');
    
    const blob = new Blob([modelsText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'orm-models.py';
    a.click();
    URL.revokeObjectURL(url);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getColumnTypeColor = (type: string) => {
    const lowerType = type.toLowerCase();
    if (lowerType.includes('int') || lowerType.includes('number')) return 'primary';
    if (lowerType.includes('varchar') || lowerType.includes('text') || lowerType.includes('string')) return 'success';
    if (lowerType.includes('date') || lowerType.includes('time')) return 'warning';
    if (lowerType.includes('bool')) return 'info';
    return 'default';
  };

  if (projectStatus !== 'complete') {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info" sx={{ mb: 2 }}>
          Database analysis is only available after transformation completion. Please complete the transformation process first.
        </Alert>
      </Box>
    );
  }

  if (loading && !analysis) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error && !analysis) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!analysis) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info" sx={{ mb: 2 }}>
          No database analysis data available. Click the button below to start analysis.
        </Alert>
        <Button variant="contained" onClick={startAnalysis} disabled={loading}>
          {loading ? 'Starting Analysis...' : 'Start Database Analysis'}
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header Stats */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="primary" fontWeight="bold">
                {analysis.analysis.total_schemas}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Database Schemas
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="success.main" fontWeight="bold">
                {analysis.analysis.total_tables}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tables
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="warning.main" fontWeight="bold">
                {Object.keys(analysis.orm_models).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ORM Models
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="database analysis tabs">
          <Tab label="Database Schema" />
          <Tab label="ORM Models" />
          <Tab label="Recommendations" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {/* Database Schema */}
          {analysis.schemas.length === 0 ? (
            <Alert severity="info">
              No database schemas found in the analysis.
            </Alert>
          ) : (
            <Box>
              {analysis.schemas.map((schema, schemaIndex) => (
                <Accordion key={schemaIndex} defaultExpanded={schemaIndex === 0}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box display="flex" alignItems="center" gap={2} flex={1}>
                      <StorageIcon color="primary" />
                      <Typography variant="h6">{schema.name}</Typography>
                      <Chip
                        label={schema.database_type}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Chip
                        label={`${schema.tables.length} tables`}
                        size="small"
                        color="info"
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    {/* Tables */}
                    <Typography variant="subtitle1" gutterBottom>
                      Tables ({schema.tables.length})
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Table Name</TableCell>
                            <TableCell>Columns</TableCell>
                            <TableCell>Primary Keys</TableCell>
                            <TableCell>Foreign Keys</TableCell>
                            <TableCell>Indexes</TableCell>
                            <TableCell>Actions</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {schema.tables.map((table, tableIndex) => (
                            <TableRow key={tableIndex} hover>
                              <TableCell>
                                <Box display="flex" alignItems="center" gap={1}>
                                  <TableChartIcon fontSize="small" />
                                  <Typography variant="body2" fontWeight="medium">
                                    {table.name}
                                  </Typography>
                                </Box>
                                {table.comment && (
                                  <Typography variant="caption" color="text.secondary">
                                    {table.comment}
                                  </Typography>
                                )}
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2">
                                  {table.columns.length}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Box display="flex" flexWrap="wrap" gap={0.5}>
                                  {table.primary_keys.map((pk, pkIndex) => (
                                    <Chip
                                      key={pkIndex}
                                      label={pk}
                                      size="small"
                                      color="primary"
                                      variant="outlined"
                                    />
                                  ))}
                                </Box>
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2">
                                  {table.foreign_keys.length}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2">
                                  {table.indexes.length}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Tooltip title="View Table Details">
                                  <IconButton
                                    size="small"
                                    onClick={() => openTableDetails(table)}
                                  >
                                    <VisibilityIcon />
                                  </IconButton>
                                </Tooltip>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>

                    {/* Views, Procedures, Functions, Triggers */}
                    {(schema.views?.length > 0 || schema.procedures?.length > 0 || 
                      schema.functions?.length > 0 || schema.triggers?.length > 0) && (
                      <Box mt={3}>
                        <Grid container spacing={2}>
                          {schema.views && schema.views.length > 0 && (
                            <Grid item xs={12} sm={6} md={3}>
                              <Paper sx={{ p: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Views ({schema.views.length})
                                </Typography>
                                <List dense>
                                  {schema.views.map((view, index) => (
                                    <ListItem key={index}>
                                      <ListItemText
                                        primary={view.name}
                                        secondary={view.type}
                                      />
                                    </ListItem>
                                  ))}
                                </List>
                              </Paper>
                            </Grid>
                          )}
                          {schema.procedures && schema.procedures.length > 0 && (
                            <Grid item xs={12} sm={6} md={3}>
                              <Paper sx={{ p: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Procedures ({schema.procedures.length})
                                </Typography>
                                <List dense>
                                  {schema.procedures.map((proc, index) => (
                                    <ListItem key={index}>
                                      <ListItemText
                                        primary={proc.name}
                                        secondary={proc.type}
                                      />
                                    </ListItem>
                                  ))}
                                </List>
                              </Paper>
                            </Grid>
                          )}
                          {schema.functions && schema.functions.length > 0 && (
                            <Grid item xs={12} sm={6} md={3}>
                              <Paper sx={{ p: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Functions ({schema.functions.length})
                                </Typography>
                                <List dense>
                                  {schema.functions.map((func, index) => (
                                    <ListItem key={index}>
                                      <ListItemText
                                        primary={func.name}
                                        secondary={func.return_type}
                                      />
                                    </ListItem>
                                  ))}
                                </List>
                              </Paper>
                            </Grid>
                          )}
                          {schema.triggers && schema.triggers.length > 0 && (
                            <Grid item xs={12} sm={6} md={3}>
                              <Paper sx={{ p: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Triggers ({schema.triggers.length})
                                </Typography>
                                <List dense>
                                  {schema.triggers.map((trigger, index) => (
                                    <ListItem key={index}>
                                      <ListItemText
                                        primary={trigger.name}
                                        secondary={`${trigger.timing} ${trigger.event}`}
                                      />
                                    </ListItem>
                                  ))}
                                </List>
                              </Paper>
                            </Grid>
                          )}
                        </Grid>
                      </Box>
                    )}
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* ORM Models */}
          {Object.keys(analysis.orm_models).length === 0 ? (
            <Alert severity="info">
              No ORM models generated from the database analysis.
            </Alert>
          ) : (
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Generated ORM Models</Typography>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={downloadOrmModels}
                >
                  Download All Models
                </Button>
              </Box>
              
              {Object.entries(analysis.orm_models).map(([modelName, modelCode]) => (
                <Accordion key={modelName}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box display="flex" alignItems="center" gap={2} flex={1}>
                      <CodeIcon color="primary" />
                      <Typography variant="h6">{modelName}</Typography>
                      <Chip label="ORM Model" size="small" color="primary" variant="outlined" />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box
                      component="pre"
                      sx={{
                        backgroundColor: '#f5f5f5',
                        p: 2,
                        borderRadius: 1,
                        overflow: 'auto',
                        fontSize: '0.875rem',
                        fontFamily: 'monospace',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {modelCode}
                    </Box>
                    <Box display="flex" justifyContent="flex-end" mt={2}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => openOrmModel(modelName, modelCode)}
                      >
                        View Full Model
                      </Button>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {/* Recommendations */}
          {analysis.recommendations.length === 0 ? (
            <Alert severity="info">
              No recommendations available for this database analysis.
            </Alert>
          ) : (
            <Box>
              {analysis.recommendations.map((recommendation, index) => (
                <Card key={index} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                      <Typography variant="h6" gutterBottom>
                        {recommendation.title}
                      </Typography>
                      <Chip
                        label={recommendation.priority}
                        color={getPriorityColor(recommendation.priority) as any}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body1" paragraph>
                      {recommendation.description}
                    </Typography>
                    
                    {recommendation.affected_tables && recommendation.affected_tables.length > 0 && (
                      <Box mb={1}>
                        <Typography variant="subtitle2" gutterBottom>
                          Affected Tables:
                        </Typography>
                        <Box display="flex" flexWrap="wrap" gap={1}>
                          {recommendation.affected_tables.map((table, tableIndex) => (
                            <Chip
                              key={tableIndex}
                              label={table}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                    
                    {recommendation.affected_columns && recommendation.affected_columns.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Affected Columns:
                        </Typography>
                        <Box display="flex" flexWrap="wrap" gap={1}>
                          {recommendation.affected_columns.map((column, columnIndex) => (
                            <Chip
                              key={columnIndex}
                              label={column}
                              size="small"
                              variant="outlined"
                              color="info"
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </TabPanel>

      </Card>

      {/* Table Details Dialog */}
      <Dialog open={!!selectedTable} onClose={() => setSelectedTable(null)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <TableChartIcon />
            Table Details: {selectedTable?.name}
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedTable && (
            <Box>
              {selectedTable.comment && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  {selectedTable.comment}
                </Alert>
              )}
              
              <Typography variant="h6" gutterBottom>
                Columns ({selectedTable.columns.length})
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Nullable</TableCell>
                      <TableCell>Primary Key</TableCell>
                      <TableCell>Unique</TableCell>
                      <TableCell>Default</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {selectedTable.columns.map((column, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {column.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={column.type}
                            size="small"
                            color={getColumnTypeColor(column.type) as any}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={column.nullable ? 'Yes' : 'No'}
                            size="small"
                            color={column.nullable ? 'default' : 'success'}
                          />
                        </TableCell>
                        <TableCell>
                          {column.primary_key && (
                            <Chip label="PK" size="small" color="primary" />
                          )}
                        </TableCell>
                        <TableCell>
                          {column.unique && (
                            <Chip label="Unique" size="small" color="info" />
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {column.default_value || '-'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedTable(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* ORM Model Dialog */}
      <Dialog open={ormDialogOpen} onClose={() => setOrmDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>ORM Model</DialogTitle>
        <DialogContent>
          <Box
            component="pre"
            sx={{
              backgroundColor: '#f5f5f5',
              p: 2,
              borderRadius: 1,
              overflow: 'auto',
              maxHeight: '60vh',
              fontSize: '0.875rem',
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
            }}
          >
            {selectedOrmModel}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOrmDialogOpen(false)}>Close</Button>
          <Button
            onClick={() => {
              navigator.clipboard.writeText(selectedOrmModel);
            }}
            variant="contained"
          >
            Copy to Clipboard
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DatabaseAnalysisComponent;