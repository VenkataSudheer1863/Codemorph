import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, CssBaseline, Box, CircularProgress } from '@mui/material';
import { theme } from './theme';
import AppShell from './components/AppShell';
import { ToastProvider } from './components/ToastProvider';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const ProjectDetail = lazy(() => import('./pages/ProjectDetail'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

function LoadingSpinner() {
  return (
    <Box
      display="flex"
      alignItems="center"
      justifyContent="center"
      minHeight="60vh"
    >
      <CircularProgress />
    </Box>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <ToastProvider>
          <BrowserRouter>
            <AppShell>
              <Suspense fallback={<LoadingSpinner />}>
                <Routes>
                  {/* Main routes */}
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/projects" element={<Dashboard />} />
                  
                  {/* Project detail with tabs */}
                  <Route path="/project/:id" element={<ProjectDetail />} />
                  <Route path="/project/:id/overview" element={<ProjectDetail />} />
                  <Route path="/project/:id/context-built" element={<ProjectDetail />} />
                  <Route path="/project/:id/stack" element={<ProjectDetail />} />
                  <Route path="/project/:id/select-stack" element={<ProjectDetail />} />
                  <Route path="/project/:id/transformation" element={<ProjectDetail />} />
                  <Route path="/project/:id/database-analysis" element={<ProjectDetail />} />
                  <Route path="/project/:id/api-analysis" element={<ProjectDetail />} />
                  <Route path="/project/:id/validation" element={<ProjectDetail />} />
                  <Route path="/project/:id/functional-preservation" element={<ProjectDetail />} />
                  
                  {/* Redirect old routes to dashboard */}
                  <Route path="/analysis" element={<Navigate to="/" replace />} />
                  <Route path="/stack-selection" element={<Navigate to="/" replace />} />
                  <Route path="/migration" element={<Navigate to="/" replace />} />
                  <Route path="/testing" element={<Navigate to="/" replace />} />
                  <Route path="/report" element={<Navigate to="/" replace />} />
                  <Route path="/logs" element={<Navigate to="/" replace />} />
                  <Route path="/new-project" element={<Navigate to="/" replace />} />
                  
                  {/* Catch all */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
            </AppShell>
          </BrowserRouter>
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
