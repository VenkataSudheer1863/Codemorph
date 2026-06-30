import { Card, CardContent, Typography, Box } from '@mui/material';
import { type ReactNode } from 'react';
import { motion } from 'framer-motion';

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  trend?: string;
  delay?: number;
}

const MotionCard = motion.create(Card);

export default function StatCard({ label, value, icon, trend, delay = 0 }: StatCardProps) {
  return (
    <MotionCard
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: [0.4, 0, 0.2, 1] }}
      sx={{
        height: '100%',
        border: '1px solid #E5E5E7',
        borderRadius: 3.5,
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
        background: '#FFFFFF',
        position: 'relative',
        overflow: 'hidden',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          borderColor: 'rgba(227,30,36,0.3)',
          boxShadow: '0 8px 24px rgba(227,30,36,0.08), 0 2px 8px rgba(0,0,0,0.04)',
          transform: 'translateY(-2px)',
        },
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          background: 'linear-gradient(90deg, #E31E24, #FF6B6F)',
          opacity: 0,
          transition: 'opacity 0.3s ease',
        },
        '&:hover::before': {
          opacity: 1,
        },
      }}
    >
      <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
        <Box display="flex" alignItems="center" gap={1.5} mb={2}>
          {icon && (
            <Box
              sx={{
                width: 44,
                height: 44,
                borderRadius: 2.5,
                backgroundColor: '#FFE5E6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#E31E24',
                flexShrink: 0,
              }}
            >
              {icon}
            </Box>
          )}
          <Box>
            <Typography
              variant="body2"
              sx={{
                color: '#86868B',
                fontWeight: 600,
                fontSize: '0.8rem',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              {label}
            </Typography>
          </Box>
        </Box>
        <Box display="flex" alignItems="baseline" gap={1}>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 800,
              color: '#1D1D1F',
              letterSpacing: '-0.02em',
              lineHeight: 1,
            }}
          >
            {typeof value === 'number' ? value.toLocaleString() : value}
          </Typography>
          {trend && (
            <Typography
              sx={{
                fontSize: '0.8rem',
                fontWeight: 600,
                color: trend.startsWith('+') ? '#10B981' : '#86868B',
              }}
            >
              {trend}
            </Typography>
          )}
        </Box>
      </CardContent>
    </MotionCard>
  );
}
