import { Chip, type ChipProps } from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  PlayCircle as RunningIcon,
  Cancel as CancelIcon,
  TouchApp as SelectIcon,
} from '@mui/icons-material';

interface StatusBadgeProps {
  status: string;
  size?: 'small' | 'medium';
}

interface StatusConfig {
  color: ChipProps['color'];
  label: string;
  icon?: React.ReactElement;
  variant?: 'filled' | 'outlined';
  sx?: Record<string, unknown>;
}

const statusConfig: Record<string, StatusConfig> = {
  created: { color: 'default', label: 'Created', icon: <PendingIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#F5F5F7', color: '#86868B' } },
  ingesting: { color: 'primary', label: 'Ingesting', icon: <RunningIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24' } },
  parsing: { color: 'primary', label: 'Parsing', icon: <RunningIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24' } },
  context_building: { color: 'primary', label: 'Building Context', icon: <RunningIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24' } },
  analyzing: { color: 'primary', label: 'Analyzing', icon: <RunningIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24' } },
  detecting: { color: 'primary', label: 'Detecting', icon: <RunningIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24' } },
  recommending: { color: 'secondary', label: 'Recommending', icon: <RunningIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24' } },
  selecting: { color: 'warning', label: 'Select Stack', icon: <SelectIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFFBEB', color: '#D97706' } },
  transforming: { color: 'primary', label: 'Transforming', icon: <RunningIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24', animation: 'pulse 2s ease-in-out infinite' } },
  complete: { color: 'success', label: 'Complete', icon: <CheckIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#ECFDF5', color: '#059669' } },
  error: { color: 'error', label: 'Error', icon: <ErrorIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24' } },
  cancelled: { color: 'default', label: 'Cancelled', icon: <CancelIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#F5F5F7', color: '#86868B' } },
  in_progress: { color: 'primary', label: 'In Progress', icon: <RunningIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24' } },
  passed: { color: 'success', label: 'Passed', icon: <CheckIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#ECFDF5', color: '#059669' } },
  failed: { color: 'error', label: 'Failed', icon: <ErrorIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24' } },
  valid: { color: 'success', label: 'Valid', icon: <CheckIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#ECFDF5', color: '#059669' } },
  invalid: { color: 'error', label: 'Invalid', icon: <ErrorIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#FFE5E6', color: '#E31E24' } },
  skipped: { color: 'default', label: 'Skipped', sx: { backgroundColor: '#F5F5F7', color: '#86868B' } },
  pending: { color: 'default', label: 'Pending', icon: <PendingIcon sx={{ fontSize: 16 }} />, sx: { backgroundColor: '#F5F5F7', color: '#86868B' } },
};

export default function StatusBadge({ status, size = 'small' }: StatusBadgeProps) {
  const config = statusConfig[status] || { color: 'default' as const, label: status, sx: {} };

  return (
    <Chip
      label={config.label}
      icon={config.icon}
      size={size}
      sx={{
        fontWeight: 700,
        borderRadius: '8px',
        height: size === 'small' ? 28 : 32,
        fontSize: size === 'small' ? '0.75rem' : '0.8rem',
        letterSpacing: '0.02em',
        border: 'none',
        ...config.sx,
        '@keyframes pulse': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.7 },
        },
      }}
    />
  );
}
