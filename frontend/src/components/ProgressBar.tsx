import { Box, LinearProgress, Typography } from '@mui/material';
import { motion } from 'framer-motion';

interface ProgressBarProps {
  value: number;
  label?: string;
  showPercent?: boolean;
  height?: number;
  animated?: boolean;
}

const MotionBox = motion.create(Box);

export default function ProgressBar({ value, label, showPercent = true, height = 8, animated = true }: ProgressBarProps) {
  return (
    <Box>
      {label && (
        <Box display="flex" justifyContent="space-between" mb={0.75}>
          <Typography
            variant="body2"
            sx={{ color: '#424245', fontWeight: 600, fontSize: '0.85rem' }}
          >
            {label}
          </Typography>
          {showPercent && (
            <Typography
              variant="body2"
              sx={{
                color: '#16a34a',
                fontWeight: 700,
                fontSize: '0.85rem',
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {Math.round(value)}%
            </Typography>
          )}
        </Box>
      )}
      {animated ? (
        <Box
          sx={{
            height,
            borderRadius: height / 2,
            backgroundColor: '#F5F5F7',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <MotionBox
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(value, 100)}%` }}
            transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
            sx={{
              height: '100%',
              borderRadius: height / 2,
              background: 'linear-gradient(90deg, #16a34a, #4ade80)',
              position: 'relative',
              '&::after': value > 0 && value < 100 ? {
                content: '""',
                position: 'absolute',
                right: 0,
                top: '50%',
                transform: 'translateY(-50%)',
                width: height + 2,
                height: height + 2,
                borderRadius: '50%',
                backgroundColor: '#16a34a',
                boxShadow: '0 0 6px rgba(22, 163, 74, 0.4)',
              } : {},
            }}
          />
        </Box>
      ) : (
        <LinearProgress
          variant="determinate"
          value={value}
          sx={{
            height,
            borderRadius: height / 2,
            backgroundColor: '#F5F5F7',
            '& .MuiLinearProgress-bar': {
              background: 'linear-gradient(90deg, #16a34a, #4ade80)',
              borderRadius: height / 2,
            },
          }}
        />
      )}
    </Box>
  );
}
