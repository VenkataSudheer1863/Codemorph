import { type ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Tooltip,
  Breadcrumbs,
  Link,
  Chip,
} from '@mui/material';
import {
  HelpOutline as HelpIcon,
  Transform as TransformIcon,
  Home as HomeIcon,
  NavigateNext as NavNextIcon,
  Notifications as NotifIcon,
} from '@mui/icons-material';

interface AppShellProps {
  children: ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const isProjectDetail = location.pathname.startsWith('/project/');

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: '#FFFFFF' }}>
      {/* Header */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          backgroundColor: 'rgba(255,255,255,0.88)',
          backdropFilter: 'blur(20px) saturate(180%)',
          borderBottom: 'none',
          boxShadow: '0 1px 0 #E5E5E7',
          zIndex: 1200,
        }}
      >
        <Toolbar sx={{ px: { xs: 2, md: 4 }, minHeight: { xs: 64, md: 70 } }}>
          <Box
            display="flex"
            alignItems="center"
            gap={1.5}
            sx={{ flexGrow: 1, cursor: 'pointer' }}
            onClick={() => navigate('/')}
          >
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: 2.5,
                background: 'linear-gradient(135deg, #E31E24 0%, #C41A1F 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(227, 30, 36, 0.3)',
                transition: 'transform 0.2s ease',
                '&:hover': { transform: 'scale(1.05)' },
              }}
            >
              <TransformIcon sx={{ fontSize: 22, color: 'white' }} />
            </Box>
            <Box>
              <Typography
                sx={{
                  fontWeight: 800,
                  fontSize: '1.15rem',
                  lineHeight: 1.2,
                  color: '#1D1D1F',
                  letterSpacing: '-0.02em',
                }}
              >
                CodeMorph
              </Typography>
              <Typography
                sx={{
                  color: '#86868B',
                  lineHeight: 1.2,
                  fontSize: '0.7rem',
                  fontWeight: 500,
                  letterSpacing: '0.02em',
                }}
              >
                AI Migration Platform
              </Typography>
            </Box>
          </Box>

          <Box display="flex" alignItems="center" gap={0.5}>
            <Tooltip title="Notifications" arrow>
              <IconButton
                size="small"
                sx={{
                  color: '#86868B',
                  width: 38,
                  height: 38,
                  '&:hover': { backgroundColor: '#F5F5F7', color: '#E31E24' },
                }}
              >
                <NotifIcon sx={{ fontSize: 20 }} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Help & Documentation" arrow>
              <IconButton
                size="small"
                sx={{
                  color: '#86868B',
                  width: 38,
                  height: 38,
                  '&:hover': { backgroundColor: '#F5F5F7', color: '#E31E24' },
                }}
              >
                <HelpIcon sx={{ fontSize: 20 }} />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>

        {isProjectDetail && (
          <Box
            sx={{
              px: { xs: 2, md: 4 },
              py: 1,
              backgroundColor: '#FAFAFA',
              borderTop: '1px solid #E5E5E7',
            }}
          >
            <Breadcrumbs
              separator={<NavNextIcon sx={{ fontSize: 16, color: '#86868B' }} />}
              sx={{ '& .MuiBreadcrumbs-separator': { mx: 0.5 } }}
            >
              <Link
                underline="hover"
                onClick={() => navigate('/')}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                  color: '#86868B',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  '&:hover': { color: '#E31E24' },
                }}
              >
                <HomeIcon sx={{ fontSize: 16 }} />
                Dashboard
              </Link>
              <Typography sx={{ color: '#1D1D1F', fontSize: '0.8rem', fontWeight: 600 }}>
                Project Details
              </Typography>
            </Breadcrumbs>
          </Box>
        )}
      </AppBar>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          mt: isProjectDetail ? '106px' : '70px',
          minHeight: 'calc(100vh - 70px - 52px)',
          backgroundColor: '#FFFFFF',
        }}
      >
        <Box sx={{ maxWidth: 1400, mx: 'auto', px: { xs: 2, sm: 3, md: 4 }, py: { xs: 3, md: 4 } }}>
          {children}
        </Box>
      </Box>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          borderTop: '1px solid #E5E5E7',
          backgroundColor: '#FAFAFA',
          py: 2,
          px: { xs: 2, md: 4 },
        }}
      >
        <Box
          sx={{
            maxWidth: 1400,
            mx: 'auto',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Typography variant="caption" sx={{ color: '#86868B', fontWeight: 500 }}>
            AI-driven application modernization
          </Typography>
          <Typography variant="caption" sx={{ color: '#D1D1D3', fontWeight: 400 }}>
            v2.0
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}
