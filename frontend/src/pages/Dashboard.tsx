import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  LinearProgress,
  Alert,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  InputAdornment,
  Tooltip,
  Fade,
  Divider,
  Select,
  FormControl,
  InputLabel,
  type SelectChangeEvent,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Folder as FolderIcon,
  GitHub as GitHubIcon,
  PlayArrow as PlayIcon,
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  CheckCircle as CompleteIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Code as CodeIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  FolderOpen as EmptyIcon,
  InsertDriveFile as FileIcon,
  DataObject as LocIcon,
} from '@mui/icons-material';
import { api } from '../api';
import StatusBadge from '../components/StatusBadge';
import StatCard from '../components/StatCard';
import { useToast } from '../components/ToastProvider';

const MotionCard = motion.create(Card);

export default function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<string | null>(null);
  const [menuAnchor, setMenuAnchor] = useState<{ [key: string]: HTMLElement | null }>({});
  const [form, setForm] = useState({ name: '', path: '', description: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('newest');

  const { data: projects = [], isLoading, refetch } = useQuery({
    queryKey: ['projects'],
    queryFn: api.listProjects,
    refetchInterval: 5000,
  });

  const createMutation = useMutation({
    mutationFn: api.createProject,
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowDialog(false);
      setForm({ name: '', path: '', description: '' });
      showToast('Project created successfully!', 'success');
      navigate(`/project/${project.id}`);
    },
    onError: (error: Error) => {
      showToast(`Failed to create project: ${error.message}`, 'error');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowDeleteDialog(false);
      setProjectToDelete(null);
      showToast('Project deleted successfully!', 'success');
    },
    onError: (error: Error) => {
      showToast(`Failed to delete project: ${error.message}`, 'error');
    },
  });

  const handleSubmit = () => {
    if (!form.name.trim() || !form.path.trim()) return;
    createMutation.mutate(form);
  };

  const handleMenuOpen = (projectId: string, event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchor({ ...menuAnchor, [projectId]: event.currentTarget });
  };

  const handleMenuClose = (projectId: string) => {
    setMenuAnchor({ ...menuAnchor, [projectId]: null });
  };

  const handleDeleteClick = (projectId: string) => {
    setProjectToDelete(projectId);
    setShowDeleteDialog(true);
    handleMenuClose(projectId);
  };

  const handleDeleteConfirm = () => {
    if (projectToDelete) {
      deleteMutation.mutate(projectToDelete);
    }
  };

  const completedCount = projects.filter((p) => p.status === 'complete').length;
  const runningCount = projects.filter((p) =>
    !['created', 'complete', 'error', 'cancelled'].includes(p.status)
  ).length;
  const totalLoc = projects.reduce((sum, p) => sum + (p.total_loc || 0), 0);

  const filteredProjects = useMemo(() => {
    let result = [...projects];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.path.toLowerCase().includes(q) ||
          (p.description && p.description.toLowerCase().includes(q))
      );
    }

    if (statusFilter !== 'all') {
      if (statusFilter === 'running') {
        result = result.filter(
          (p) => !['created', 'complete', 'error', 'cancelled'].includes(p.status)
        );
      } else {
        result = result.filter((p) => p.status === statusFilter);
      }
    }

    result.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'oldest':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'name':
          return a.name.localeCompare(b.name);
        case 'files':
          return (b.total_files || 0) - (a.total_files || 0);
        default:
          return 0;
      }
    });

    return result;
  }, [projects, searchQuery, statusFilter, sortBy]);

  return (
    <Box>
      {/* Hero Header */}
      <Box
        sx={{
          mb: 4,
          pb: 4,
          borderBottom: '1px solid #E5E5E7',
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <Typography
                variant="h3"
                sx={{
                  fontWeight: 800,
                  letterSpacing: '-0.03em',
                  mb: 1,
                  background: 'linear-gradient(135deg, #1D1D1F 0%, #424245 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Migration Dashboard
              </Typography>
            </motion.div>
            <Typography variant="body1" sx={{ color: '#86868B', fontWeight: 400, fontSize: '1.05rem' }}>
              Monitor and manage your AI-powered application modernization projects
            </Typography>
          </Box>
          <Box display="flex" gap={1.5} alignItems="center">
            <Tooltip title="Refresh projects" arrow>
              <IconButton
                onClick={() => refetch()}
                sx={{
                  border: '1px solid #E5E5E7',
                  borderRadius: 2.5,
                  width: 42,
                  height: 42,
                  '&:hover': { borderColor: '#E31E24', color: '#E31E24' },
                }}
              >
                <RefreshIcon sx={{ fontSize: 20 }} />
              </IconButton>
            </Tooltip>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setShowDialog(true)}
              sx={{
                height: 42,
                px: 3,
                borderRadius: 2.5,
                background: 'linear-gradient(135deg, #E31E24 0%, #C41A1F 100%)',
                boxShadow: '0 2px 8px rgba(227, 30, 36, 0.3)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #C41A1F 0%, #A8161A 100%)',
                  boxShadow: '0 4px 14px rgba(227, 30, 36, 0.4)',
                },
              }}
            >
              New Project
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Stats Row */}
      <Grid container spacing={2.5} mb={4}>
        <Grid item xs={6} sm={6} md={3}>
          <StatCard label="Total Projects" value={projects.length} icon={<FolderIcon />} delay={0} />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatCard label="Completed" value={completedCount} icon={<CompleteIcon />} delay={0.1} />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatCard label="In Progress" value={runningCount} icon={<ScheduleIcon />} delay={0.2} />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatCard label="Total LOC" value={totalLoc} icon={<CodeIcon />} delay={0.3} />
        </Grid>
      </Grid>

      {/* Search, Filter & Sort */}
      <Box
        sx={{
          display: 'flex',
          gap: 2,
          mb: 3,
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <TextField
          placeholder="Search projects..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          size="small"
          sx={{
            flex: 1,
            minWidth: 200,
            '& .MuiOutlinedInput-root': {
              borderRadius: 2.5,
              backgroundColor: '#FAFAFA',
            },
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: '#86868B', fontSize: 20 }} />
              </InputAdornment>
            ),
          }}
        />
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel sx={{ fontSize: '0.85rem' }}>
            <Box display="flex" alignItems="center" gap={0.5}>
              <FilterIcon sx={{ fontSize: 16 }} />
              Status
            </Box>
          </InputLabel>
          <Select
            value={statusFilter}
            label="Status"
            onChange={(e: SelectChangeEvent) => setStatusFilter(e.target.value)}
            sx={{ borderRadius: 2.5, backgroundColor: '#FAFAFA' }}
          >
            <MenuItem value="all">All Status</MenuItem>
            <MenuItem value="created">Created</MenuItem>
            <MenuItem value="running">In Progress</MenuItem>
            <MenuItem value="complete">Completed</MenuItem>
            <MenuItem value="error">Failed</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel sx={{ fontSize: '0.85rem' }}>
            <Box display="flex" alignItems="center" gap={0.5}>
              <SortIcon sx={{ fontSize: 16 }} />
              Sort
            </Box>
          </InputLabel>
          <Select
            value={sortBy}
            label="Sort"
            onChange={(e: SelectChangeEvent) => setSortBy(e.target.value)}
            sx={{ borderRadius: 2.5, backgroundColor: '#FAFAFA' }}
          >
            <MenuItem value="newest">Newest First</MenuItem>
            <MenuItem value="oldest">Oldest First</MenuItem>
            <MenuItem value="name">By Name</MenuItem>
            <MenuItem value="files">By File Count</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Results Count */}
      {searchQuery || statusFilter !== 'all' ? (
        <Box mb={2}>
          <Typography variant="body2" sx={{ color: '#86868B', fontWeight: 500 }}>
            Showing {filteredProjects.length} of {projects.length} projects
            {searchQuery && (
              <Chip
                label={`"${searchQuery}"`}
                size="small"
                onDelete={() => setSearchQuery('')}
                sx={{ ml: 1, height: 24, fontSize: '0.75rem' }}
              />
            )}
          </Typography>
        </Box>
      ) : null}

      {/* Projects Grid */}
      {isLoading ? (
        <Box>
          <LinearProgress sx={{ borderRadius: 1, mb: 3 }} />
          <Grid container spacing={2.5}>
            {[1, 2, 3].map((i) => (
              <Grid item xs={12} sm={6} md={4} key={i}>
                <Card sx={{ height: 220, p: 3 }}>
                  <Box className="animate-shimmer" sx={{ height: 20, width: '60%', borderRadius: 1, mb: 2 }} />
                  <Box className="animate-shimmer" sx={{ height: 14, width: '80%', borderRadius: 1, mb: 1 }} />
                  <Box className="animate-shimmer" sx={{ height: 14, width: '40%', borderRadius: 1, mb: 3 }} />
                  <Box className="animate-shimmer" sx={{ height: 36, borderRadius: 1 }} />
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      ) : filteredProjects.length === 0 ? (
        <Fade in>
          <Card
            sx={{
              textAlign: 'center',
              py: 10,
              border: '2px dashed #E5E5E7',
              backgroundColor: '#FAFAFA',
              boxShadow: 'none',
            }}
          >
            <EmptyIcon sx={{ fontSize: 72, color: '#D1D1D3', mb: 2 }} />
            <Typography variant="h6" sx={{ color: '#86868B', fontWeight: 600, mb: 1 }}>
              {projects.length === 0 ? 'No projects yet' : 'No matching projects'}
            </Typography>
            <Typography variant="body2" sx={{ color: '#86868B', mb: 3, maxWidth: 360, mx: 'auto' }}>
              {projects.length === 0
                ? 'Create your first project to begin AI-powered code migration'
                : 'Try adjusting your search or filter criteria'}
            </Typography>
            {projects.length === 0 && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setShowDialog(true)}
                sx={{
                  background: 'linear-gradient(135deg, #E31E24 0%, #C41A1F 100%)',
                  boxShadow: '0 2px 8px rgba(227, 30, 36, 0.3)',
                }}
              >
                Create First Project
              </Button>
            )}
          </Card>
        </Fade>
      ) : (
        <Grid container spacing={2.5}>
          <AnimatePresence>
            {filteredProjects.map((project, idx) => (
              <Grid item xs={12} sm={6} md={4} key={project.id}>
                <MotionCard
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.35, delay: idx * 0.05, ease: [0.4, 0, 0.2, 1] }}
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: 3.5,
                    border: '1px solid #E5E5E7',
                    position: 'relative',
                    overflow: 'hidden',
                    cursor: 'pointer',
                    '&:hover': {
                      borderColor: 'rgba(227,30,36,0.3)',
                      boxShadow: '0 12px 32px rgba(227,30,36,0.08), 0 4px 12px rgba(0,0,0,0.04)',
                      transform: 'translateY(-4px)',
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: 3,
                      background:
                        project.status === 'complete'
                          ? 'linear-gradient(90deg, #10B981, #34D399)'
                          : project.status === 'error'
                          ? 'linear-gradient(90deg, #E31E24, #FF6B6F)'
                          : ['created', 'cancelled'].includes(project.status)
                          ? 'linear-gradient(90deg, #D1D1D3, #E5E5E7)'
                          : 'linear-gradient(90deg, #E31E24, #FF6B6F)',
                    },
                  }}
                  onClick={() => navigate(`/project/${project.id}`)}
                >
                  <CardContent sx={{ flex: 1, p: 3, pb: 1 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1.5}>
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 700,
                          fontSize: '1.05rem',
                          flex: 1,
                          mr: 1,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          color: '#1D1D1F',
                        }}
                      >
                        {project.name}
                      </Typography>
                      <StatusBadge status={project.status} />
                    </Box>

                    {project.description && (
                      <Typography
                        variant="body2"
                        sx={{
                          color: '#86868B',
                          mb: 2,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          fontSize: '0.85rem',
                          lineHeight: 1.5,
                        }}
                      >
                        {project.description}
                      </Typography>
                    )}

                    <Chip
                      icon={project.path.startsWith('http') ? <GitHubIcon sx={{ fontSize: 14 }} /> : <FolderIcon sx={{ fontSize: 14 }} />}
                      label={project.path.startsWith('http') ? 'Git Repository' : 'Local'}
                      size="small"
                      variant="outlined"
                      sx={{
                        mb: 1.5,
                        height: 26,
                        fontSize: '0.75rem',
                        borderColor: '#E5E5E7',
                        color: '#86868B',
                      }}
                    />

                    <Typography
                      variant="caption"
                      sx={{
                        fontFamily: '"JetBrains Mono", monospace',
                        display: 'block',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        color: '#86868B',
                        fontSize: '0.75rem',
                      }}
                    >
                      {project.path}
                    </Typography>
                  </CardContent>

                  {((project.total_files || 0) > 0 || (project.total_loc || 0) > 0) && (
                    <Box
                      sx={{
                        px: 3,
                        py: 1.5,
                        borderTop: '1px solid #F5F5F7',
                        display: 'flex',
                        gap: 2.5,
                        backgroundColor: '#FAFAFA',
                      }}
                    >
                      {(project.total_files || 0) > 0 && (
                        <Box display="flex" alignItems="center" gap={0.5}>
                          <FileIcon sx={{ fontSize: 14, color: '#86868B' }} />
                          <Typography variant="caption" sx={{ color: '#86868B', fontWeight: 500 }}>
                            {project.total_files || 0} files
                          </Typography>
                        </Box>
                      )}
                      {(project.total_loc || 0) > 0 && (
                        <Box display="flex" alignItems="center" gap={0.5}>
                          <LocIcon sx={{ fontSize: 14, color: '#86868B' }} />
                          <Typography variant="caption" sx={{ color: '#86868B', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>
                            {(project.total_loc || 0).toLocaleString()} LOC
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  )}

                  <CardActions
                    sx={{
                      p: 2,
                      pt: 0,
                      display: 'flex',
                      justifyContent: 'space-between',
                      backgroundColor: ((project.total_files || 0) > 0 || (project.total_loc || 0) > 0) ? '#FAFAFA' : 'transparent',
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => navigate(`/project/${project.id}`)}
                      sx={{
                        flex: 1,
                        mr: 1,
                        borderRadius: 2,
                        borderColor: '#E5E5E7',
                        color: '#424245',
                        '&:hover': {
                          borderColor: '#E31E24',
                          color: '#E31E24',
                          backgroundColor: 'rgba(227,30,36,0.04)',
                        },
                      }}
                    >
                      View Details
                    </Button>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(project.id, e)}
                      sx={{
                        color: '#86868B',
                        width: 34,
                        height: 34,
                        '&:hover': { backgroundColor: '#F5F5F7' },
                      }}
                    >
                      <MoreVertIcon sx={{ fontSize: 18 }} />
                    </IconButton>
                    <Menu
                      anchorEl={menuAnchor[project.id]}
                      open={Boolean(menuAnchor[project.id])}
                      onClose={() => handleMenuClose(project.id)}
                      transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                      anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                    >
                      <MenuItem
                        onClick={() => {
                          navigate(`/project/${project.id}`);
                          handleMenuClose(project.id);
                        }}
                      >
                        <ListItemIcon>
                          <ViewIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText>View Details</ListItemText>
                      </MenuItem>
                      <Divider sx={{ my: 0.5 }} />
                      <MenuItem
                        onClick={() => handleDeleteClick(project.id)}
                        sx={{ color: '#E31E24' }}
                      >
                        <ListItemIcon>
                          <DeleteIcon fontSize="small" sx={{ color: '#E31E24' }} />
                        </ListItemIcon>
                        <ListItemText>Delete Project</ListItemText>
                      </MenuItem>
                    </Menu>
                  </CardActions>
                </MotionCard>
              </Grid>
            ))}
          </AnimatePresence>
        </Grid>
      )}

      {/* Create Project Dialog */}
      <Dialog open={showDialog} onClose={() => setShowDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #E31E24 0%, #C41A1F 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <AddIcon sx={{ color: 'white', fontSize: 20 }} />
          </Box>
          New Project
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ color: '#86868B', mb: 3 }}>
            Enter your project details below to start the AI-powered migration analysis.
          </Typography>
          <Box display="flex" flexDirection="column" gap={2.5}>
            {createMutation.isError && (
              <Alert severity="error" onClose={() => createMutation.reset()}>
                {createMutation.error?.message || 'Failed to create project'}
              </Alert>
            )}
            <TextField
              label="Project Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="My Legacy Application"
              fullWidth
              required
            />
            <TextField
              label="Source Path or Git URL"
              value={form.path}
              onChange={(e) => setForm({ ...form, path: e.target.value })}
              placeholder="C:\projects\legacy-app or https://github.com/..."
              fullWidth
              required
              InputProps={{
                sx: { fontFamily: '"JetBrains Mono", monospace', fontSize: '0.9rem' },
              }}
            />
            <TextField
              label="Description (Optional)"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Brief description of the project and migration goals..."
              multiline
              rows={3}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDialog(false)} sx={{ color: '#86868B' }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={createMutation.isPending || !form.name.trim() || !form.path.trim()}
            startIcon={createMutation.isPending ? undefined : <PlayIcon />}
            sx={{
              background: 'linear-gradient(135deg, #E31E24 0%, #C41A1F 100%)',
              '&:hover': { background: 'linear-gradient(135deg, #C41A1F 0%, #A8161A 100%)' },
            }}
          >
            {createMutation.isPending ? 'Creating...' : 'Create & Start'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onClose={() => setShowDeleteDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: 2,
              backgroundColor: '#FFE5E6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ErrorIcon sx={{ color: '#E31E24', fontSize: 20 }} />
          </Box>
          Delete Project
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2, borderRadius: 2.5 }}>
            This action cannot be undone. All project data, including analysis results,
            transformation mappings, and generated artifacts will be permanently deleted.
          </Alert>
          <Typography variant="body1" sx={{ color: '#424245' }}>
            Are you sure you want to delete this project?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDeleteDialog(false)} disabled={deleteMutation.isPending} sx={{ color: '#86868B' }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDeleteConfirm}
            disabled={deleteMutation.isPending}
            startIcon={<DeleteIcon />}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete Project'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
