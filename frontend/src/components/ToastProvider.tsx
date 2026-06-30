import { createContext, useContext, useState, type ReactNode } from 'react';
import { Snackbar, Alert, type AlertColor, Slide, type SlideProps } from '@mui/material';

interface Toast {
  message: string;
  severity: AlertColor;
}

interface ToastContextType {
  showToast: (message: string, severity?: AlertColor) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}

function SlideTransition(props: SlideProps) {
  return <Slide {...props} direction="up" />;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<Toast | null>(null);

  const showToast = (message: string, severity: AlertColor = 'info') => {
    setToast({ message, severity });
  };

  const handleClose = () => {
    setToast(null);
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <Snackbar
        open={!!toast}
        autoHideDuration={5000}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        TransitionComponent={SlideTransition}
      >
        <Alert
          onClose={handleClose}
          severity={toast?.severity}
          variant="filled"
          sx={{
            width: '100%',
            borderRadius: 3,
            fontWeight: 600,
            boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
            alignItems: 'center',
          }}
        >
          {toast?.message}
        </Alert>
      </Snackbar>
    </ToastContext.Provider>
  );
}
