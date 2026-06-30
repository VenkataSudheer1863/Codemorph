import { createTheme, alpha } from '@mui/material/styles';

const BRAND_RED = '#E31E24';
const BRAND_RED_DARK = '#C41A1F';
const BRAND_RED_LIGHT = '#FFE5E6';
const BRAND_RED_GLOW = 'rgba(227, 30, 36, 0.08)';
const PURE_WHITE = '#FFFFFF';
const SNOW_WHITE = '#FAFAFA';
const LIGHT_GRAY = '#F5F5F7';
const JET_BLACK = '#1D1D1F';
const CHARCOAL = '#424245';
const MEDIUM_GRAY = '#86868B';
const BORDER_GRAY = '#E5E5E7';
const BORDER_DARK = '#D1D1D3';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: BRAND_RED,
      light: BRAND_RED_LIGHT,
      dark: BRAND_RED_DARK,
      contrastText: PURE_WHITE,
    },
    secondary: {
      main: CHARCOAL,
      light: LIGHT_GRAY,
      dark: JET_BLACK,
      contrastText: PURE_WHITE,
    },
    success: {
      main: '#10B981',
      light: '#ECFDF5',
      dark: '#059669',
      contrastText: PURE_WHITE,
    },
    warning: {
      main: '#F59E0B',
      light: '#FFFBEB',
      dark: '#D97706',
      contrastText: PURE_WHITE,
    },
    error: {
      main: BRAND_RED,
      light: BRAND_RED_LIGHT,
      dark: BRAND_RED_DARK,
      contrastText: PURE_WHITE,
    },
    info: {
      main: '#3B82F6',
      light: '#EFF6FF',
      dark: '#2563EB',
      contrastText: PURE_WHITE,
    },
    background: {
      default: PURE_WHITE,
      paper: PURE_WHITE,
    },
    divider: BORDER_GRAY,
    text: {
      primary: JET_BLACK,
      secondary: CHARCOAL,
      disabled: MEDIUM_GRAY,
    },
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    h1: { fontWeight: 800, color: JET_BLACK, letterSpacing: '-0.025em' },
    h2: { fontWeight: 800, color: JET_BLACK, letterSpacing: '-0.025em' },
    h3: { fontWeight: 700, color: JET_BLACK, letterSpacing: '-0.02em' },
    h4: { fontWeight: 700, color: JET_BLACK, letterSpacing: '-0.015em' },
    h5: { fontWeight: 700, color: JET_BLACK, letterSpacing: '-0.01em' },
    h6: { fontWeight: 700, color: JET_BLACK },
    subtitle1: { fontWeight: 600, color: CHARCOAL },
    subtitle2: { fontWeight: 600, color: CHARCOAL, fontSize: '0.875rem' },
    body1: { color: CHARCOAL, lineHeight: 1.7 },
    body2: { color: CHARCOAL, lineHeight: 1.6 },
    caption: { color: MEDIUM_GRAY, fontSize: '0.8rem' },
    button: { textTransform: 'none' as const, fontWeight: 600, letterSpacing: '0.01em' },
  },
  shadows: [
    'none',
    '0 1px 2px rgba(0,0,0,0.04)',
    '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
    '0 4px 6px -1px rgba(0,0,0,0.06), 0 2px 4px -1px rgba(0,0,0,0.04)',
    '0 6px 12px -2px rgba(0,0,0,0.06), 0 3px 7px -3px rgba(0,0,0,0.05)',
    '0 10px 15px -3px rgba(0,0,0,0.06), 0 4px 6px -2px rgba(0,0,0,0.04)',
    '0 12px 20px -4px rgba(0,0,0,0.08), 0 4px 8px -2px rgba(0,0,0,0.04)',
    '0 14px 28px rgba(0,0,0,0.08), 0 10px 10px rgba(0,0,0,0.04)',
    '0 16px 32px -4px rgba(0,0,0,0.1), 0 6px 16px -4px rgba(0,0,0,0.06)',
    '0 20px 40px -4px rgba(0,0,0,0.1), 0 8px 20px -4px rgba(0,0,0,0.06)',
    '0 24px 48px -6px rgba(0,0,0,0.12), 0 12px 24px -4px rgba(0,0,0,0.06)',
    ...Array(14).fill('0 28px 56px -6px rgba(0,0,0,0.12), 0 14px 28px -4px rgba(0,0,0,0.06)'),
  ] as unknown as typeof createTheme extends (o: infer T) => unknown ? T extends { shadows?: infer S } ? S : never : never,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: PURE_WHITE,
          '& ::selection': {
            backgroundColor: BRAND_RED_LIGHT,
            color: BRAND_RED,
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          fontWeight: 600,
          padding: '10px 24px',
          boxShadow: 'none',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            boxShadow: 'none',
            transform: 'translateY(-1px)',
          },
          '&:active': {
            transform: 'translateY(0)',
          },
        },
        contained: {
          backgroundColor: BRAND_RED,
          color: PURE_WHITE,
          '&:hover': {
            backgroundColor: BRAND_RED_DARK,
            boxShadow: `0 4px 14px ${alpha(BRAND_RED, 0.4)}`,
          },
        },
        outlined: {
          borderColor: BORDER_GRAY,
          color: CHARCOAL,
          borderWidth: 1.5,
          '&:hover': {
            borderColor: BRAND_RED,
            color: BRAND_RED,
            backgroundColor: BRAND_RED_GLOW,
            borderWidth: 1.5,
          },
        },
        text: {
          color: CHARCOAL,
          '&:hover': {
            backgroundColor: LIGHT_GRAY,
            color: BRAND_RED,
          },
        },
        sizeSmall: {
          padding: '6px 16px',
          fontSize: '0.8125rem',
        },
        sizeLarge: {
          padding: '12px 32px',
          fontSize: '1rem',
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          color: CHARCOAL,
          borderRadius: 10,
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: LIGHT_GRAY,
            color: BRAND_RED,
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 10,
            backgroundColor: PURE_WHITE,
            transition: 'all 0.2s ease',
            '& fieldset': {
              borderColor: BORDER_GRAY,
              borderWidth: 1.5,
              transition: 'all 0.2s ease',
            },
            '&:hover fieldset': {
              borderColor: BORDER_DARK,
            },
            '&.Mui-focused fieldset': {
              borderColor: BRAND_RED,
              borderWidth: 2,
            },
          },
          '& .MuiInputLabel-root.Mui-focused': {
            color: BRAND_RED,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: PURE_WHITE,
          border: `1px solid ${BORDER_GRAY}`,
          borderRadius: 14,
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          overflow: 'hidden',
          '&:hover': {
            borderColor: alpha(BRAND_RED, 0.3),
            boxShadow: `0 8px 24px ${alpha(BRAND_RED, 0.08)}, 0 2px 8px rgba(0,0,0,0.04)`,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          fontSize: '0.75rem',
          borderRadius: 8,
          height: 28,
        },
        filled: {
          '&.MuiChip-colorPrimary': { backgroundColor: BRAND_RED, color: PURE_WHITE },
          '&.MuiChip-colorSecondary': { backgroundColor: LIGHT_GRAY, color: CHARCOAL },
          '&.MuiChip-colorSuccess': { backgroundColor: '#ECFDF5', color: '#059669' },
          '&.MuiChip-colorWarning': { backgroundColor: '#FFFBEB', color: '#D97706' },
          '&.MuiChip-colorError': { backgroundColor: BRAND_RED_LIGHT, color: BRAND_RED },
        },
        outlined: {
          borderWidth: 1.5,
          '&.MuiChip-colorPrimary': { borderColor: alpha(BRAND_RED, 0.4), color: BRAND_RED },
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: { borderRadius: 6, height: 8, backgroundColor: LIGHT_GRAY },
        bar: { backgroundColor: BRAND_RED, borderRadius: 6 },
      },
    },
    MuiCircularProgress: {
      styleOverrides: { root: { color: BRAND_RED } },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(255,255,255,0.85)',
          backdropFilter: 'blur(20px) saturate(180%)',
          color: JET_BLACK,
          borderBottom: 'none',
          boxShadow: `0 1px 0 ${BORDER_GRAY}`,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none' as const,
          fontWeight: 600,
          fontSize: '0.9rem',
          color: MEDIUM_GRAY,
          borderRadius: 8,
          minHeight: 42,
          padding: '8px 18px',
          transition: 'all 0.2s ease',
          '&.Mui-selected': { color: BRAND_RED },
          '&:hover': { color: BRAND_RED, backgroundColor: BRAND_RED_GLOW },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: { backgroundColor: BRAND_RED, height: 3, borderRadius: '3px 3px 0 0' },
        flexContainer: { gap: 4 },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: SNOW_WHITE,
          '& .MuiTableCell-head': {
            color: MEDIUM_GRAY,
            fontWeight: 600,
            fontSize: '0.8rem',
            textTransform: 'uppercase' as const,
            letterSpacing: '0.05em',
            borderBottom: `2px solid ${BORDER_GRAY}`,
            padding: '14px 16px',
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          transition: 'background-color 0.15s ease',
          '&:hover': { backgroundColor: BRAND_RED_GLOW },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { borderBottom: `1px solid ${BORDER_GRAY}`, color: CHARCOAL, padding: '14px 16px' },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 12, fontWeight: 500 },
        filledError: { backgroundColor: BRAND_RED, color: PURE_WHITE },
        filledSuccess: { backgroundColor: '#10B981', color: PURE_WHITE },
        filledWarning: { backgroundColor: '#F59E0B', color: PURE_WHITE },
        filledInfo: { backgroundColor: '#3B82F6', color: PURE_WHITE },
        standardError: { backgroundColor: BRAND_RED_LIGHT, color: BRAND_RED_DARK, border: `1px solid ${alpha(BRAND_RED, 0.2)}` },
        standardSuccess: { backgroundColor: '#ECFDF5', color: '#059669', border: '1px solid rgba(16,185,129,0.2)' },
        standardWarning: { backgroundColor: '#FFFBEB', color: '#D97706', border: '1px solid rgba(245,158,11,0.2)' },
        standardInfo: { backgroundColor: '#EFF6FF', color: '#2563EB', border: '1px solid rgba(59,130,246,0.2)' },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
          boxShadow: '0 24px 48px -12px rgba(0,0,0,0.18)',
          border: `1px solid ${BORDER_GRAY}`,
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: { color: JET_BLACK, fontWeight: 700, fontSize: '1.35rem', padding: '24px 24px 16px' },
      },
    },
    MuiDialogContent: {
      styleOverrides: { root: { padding: '8px 24px 24px' } },
    },
    MuiDialogActions: {
      styleOverrides: { root: { padding: '16px 24px 24px', gap: 8 } },
    },
    MuiStepper: {
      styleOverrides: { root: { padding: '24px 0' } },
    },
    MuiStepIcon: {
      styleOverrides: {
        root: {
          color: BORDER_GRAY,
          '&.Mui-active': { color: BRAND_RED },
          '&.Mui-completed': { color: '#10B981' },
        },
      },
    },
    MuiStepLabel: {
      styleOverrides: {
        label: {
          color: MEDIUM_GRAY,
          fontSize: '0.8rem',
          fontWeight: 500,
          '&.Mui-active': { color: BRAND_RED, fontWeight: 700 },
          '&.Mui-completed': { color: '#10B981', fontWeight: 600 },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: JET_BLACK,
          color: PURE_WHITE,
          fontSize: '0.8rem',
          borderRadius: 8,
          padding: '8px 14px',
          fontWeight: 500,
        },
        arrow: { color: JET_BLACK },
      },
    },
    MuiRadio: {
      styleOverrides: {
        root: { color: BORDER_DARK, '&.Mui-checked': { color: BRAND_RED } },
      },
    },
    MuiCheckbox: {
      styleOverrides: {
        root: { color: BORDER_DARK, '&.Mui-checked': { color: BRAND_RED } },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        switchBase: {
          '&.Mui-checked': {
            color: BRAND_RED,
            '& + .MuiSwitch-track': { backgroundColor: BRAND_RED },
          },
        },
      },
    },
    MuiAccordion: {
      styleOverrides: {
        root: {
          borderRadius: '12px !important',
          border: `1px solid ${BORDER_GRAY}`,
          boxShadow: 'none',
          '&:before': { display: 'none' },
          '&.Mui-expanded': { margin: '0 0 12px 0', borderColor: alpha(BRAND_RED, 0.3) },
        },
      },
    },
    MuiAccordionSummary: {
      styleOverrides: {
        root: { borderRadius: 12, '&:hover': { backgroundColor: BRAND_RED_GLOW } },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          borderRadius: 12,
          border: `1px solid ${BORDER_GRAY}`,
          boxShadow: '0 10px 30px -5px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
          marginTop: 4,
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '2px 6px',
          padding: '8px 12px',
          '&:hover': { backgroundColor: BRAND_RED_GLOW },
        },
      },
    },
  },
});
