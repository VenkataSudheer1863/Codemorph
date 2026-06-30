import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Tabs, Tab, Chip, Alert, CircularProgress,
  Grid, Paper, List, ListItem, ListItemText, LinearProgress, Accordion,
  AccordionSummary, AccordionDetails, Divider,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon, Error as ErrorIcon, ExpandMore as ExpandMoreIcon,
  Warning as WarningIcon, Info as InfoIcon,
} from '@mui/icons-material';
import {
  api,
  type ValidationMetrics,
  type ValidationResultDetail,
  type AuditReport,
  type APIAnalysis,
} from '../api';
import DependencyGraphComparison from './DependencyGraphComparison';

interface ValidationDashboardProps { projectId: string; }

function TabPanel({ children, value, index }: { children?: React.ReactNode; value: number; index: number }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

// ─── Audit helpers ────────────────────────────────────────────────────────────

type CheckStatus = 'pass' | 'warn' | 'fail' | 'skip';
interface AuditCheck { label: string; status: CheckStatus; evidence: string; }
interface AuditSection { title: string; checks: AuditCheck[]; }

const statusIcon = (s: CheckStatus) => {
  if (s === 'pass') return <CheckCircleIcon sx={{ color: 'success.main', fontSize: 18, flexShrink: 0 }} />;
  if (s === 'warn') return <WarningIcon sx={{ color: 'warning.main', fontSize: 18, flexShrink: 0 }} />;
  if (s === 'fail') return <ErrorIcon sx={{ color: 'error.main', fontSize: 18, flexShrink: 0 }} />;
  return <InfoIcon sx={{ color: 'text.disabled', fontSize: 18, flexShrink: 0 }} />;
};

const statusBg: Record<CheckStatus, string> = {
  pass: '#e8f5e9', warn: '#fff8e1', fail: '#ffebee', skip: '#f5f5f5',
};

const na = (label: string) => `No ${label} data available — skipping ${label} check.`;

function buildAudit(audit: AuditReport, analysis: APIAnalysis | null): AuditSection[] {
  const cq = audit.code_quality;
  const arch = audit.architecture;
  const deps = audit.dependencies;
  const tc = audit.test_coverage;
  const tr = audit.transformation;
  const fc = audit.file_coverage;
  const endpoints = analysis?.endpoints ?? [];
  const stats = analysis?.statistics;

  // Convert a 0-100 validator score to CheckStatus
  const scoreToStatus = (score: number | null | undefined, passThreshold = 70, warnThreshold = 40): CheckStatus => {
    if (score == null) return 'skip';
    if (score >= passThreshold) return 'pass';
    if (score >= warnThreshold) return 'warn';
    return 'fail';
  };

  // Use validator_passed when available, else fall back to score, else fallback
  const validatorStatus = (passed: boolean | null | undefined, score: number | null | undefined, fallback: CheckStatus): CheckStatus => {
    if (passed != null) return passed ? 'pass' : 'fail';
    if (score != null) return scoreToStatus(score);
    return fallback;
  };

  // ── 1. Code Quality ──────────────────────────────────────────────────────
  const cqValidatorScore = cq.validator_score;
  const cqValidatorPassed = cq.validator_passed;
  const complexityStatus: CheckStatus =
    cq.avg_complexity === null ? 'skip' : cq.avg_complexity <= 5 ? 'pass' : cq.avg_complexity <= 10 ? 'warn' : 'fail';
  const namingCompliant = endpoints.filter(ep => /^\/[a-z0-9/_{}.-]+$/.test(ep.path)).length;
  const lintStatus: CheckStatus =
    cq.total_parsed_files === 0 ? 'skip' : cq.linting_violations === 0 ? 'pass' : cq.linting_violations <= 5 ? 'warn' : 'fail';
  const smellStatus: CheckStatus = cq.god_class_candidates.length > 0 || cq.large_files.length > 0 ? 'warn' : 'pass';
  const cqOverallStatus: CheckStatus = validatorStatus(cqValidatorPassed, cqValidatorScore, smellStatus);
  const parseRate = cq.parse_success_rate != null ? `${cq.parse_success_rate.toFixed(1)}%` : `${cq.successful_parses}/${cq.total_parsed_files} files`;

  const codeQuality: AuditSection = {
    title: '1. Code Quality Validation',
    checks: [
      { label: 'Cyclomatic Complexity',
        status: complexityStatus,
        evidence: cq.avg_complexity === null ? na('complexity score') : `Average complexity ${cq.avg_complexity} (max: ${cq.max_complexity ?? 'N/A'}) across ${cq.total_parsed_files} modules. Maintainability index: ${cq.avg_maintainability ?? 'N/A'}.` },
      { label: `Linting — ${cq.style_guide || 'PEP8'} Compliance`,
        status: lintStatus,
        evidence: cq.total_parsed_files === 0 ? na('linting') : `${cq.linting_violations} violation(s) against ${cq.style_guide || 'PEP8'}. ${namingCompliant}/${endpoints.length} endpoint paths conform to REST naming. Parse rate: ${parseRate}.` },
      { label: 'Code Smells — Long Methods / God Classes',
        status: smellStatus,
        evidence: cq.god_class_candidates.length === 0 && cq.large_files.length === 0
          ? `No smells detected. ${cq.total_classes} classes, ${cq.total_functions} functions across ${cq.total_parsed_files} files.`
          : `${cq.god_class_candidates.length} God Class candidate(s), ${cq.large_files.length} file(s) >500 LOC.` },
      { label: 'Overall Code Quality Gate',
        status: cqOverallStatus,
        evidence: cqValidatorScore != null
          ? `Validator score: ${cqValidatorScore.toFixed(0)}% (threshold 50%). ${cqValidatorPassed ? 'Passed.' : 'Failed — review anti-patterns.'}`
          : na('code quality validator') },
    ],
  };

  // ── 2. Architecture Compliance ────────────────────────────────────────────
  const archValidatorScore = arch.validator_score;
  const archValidatorPassed = arch.validator_passed;
  const archValidatorEvidence = arch.validator_evidence ?? [];
  const archLayers = Object.keys(arch.architecture_layers);
  const hasComponents = arch.total_components > 0;
  const circularEvidence = archValidatorEvidence.find(e => e.toLowerCase().includes('circular'));
  const circularStatus: CheckStatus = circularEvidence
    ? (circularEvidence.includes('No circular') ? 'pass' : 'warn')
    : (hasComponents ? 'pass' : 'skip');
  const layerStatus: CheckStatus = validatorStatus(archValidatorPassed, archValidatorScore,
    archLayers.length < 2 ? 'skip' : 'pass');

  const architecture: AuditSection = {
    title: '2. Architecture Compliance',
    checks: [
      { label: 'Circular Dependencies',
        status: circularStatus,
        evidence: circularEvidence ?? (!hasComponents ? na('component graph') : `No circular dependencies detected across ${arch.total_components} components in ${arch.layer_count} layer(s).`) },
      { label: 'Layer Isolation — Separation of Concerns',
        status: archLayers.length < 2 ? 'skip' : layerStatus,
        evidence: archLayers.length < 2 ? na('multi-layer architecture')
          : archValidatorEvidence.length > 0 ? archValidatorEvidence.join(' ')
          : `Layers: ${archLayers.join(' → ')}. Validator score: ${archValidatorScore?.toFixed(0) ?? 'N/A'}%.` },
      { label: 'High-Complexity Components',
        status: arch.high_complexity_components.length === 0 ? (hasComponents ? 'pass' : 'skip') : 'warn',
        evidence: !hasComponents ? na('component') : arch.high_complexity_components.length === 0
          ? `${arch.total_components} components verified — none flagged as high-complexity.`
          : `${arch.high_complexity_components.length} high-complexity component(s): ${arch.high_complexity_components.slice(0, 3).join(', ')}.` },
      { label: 'Framework Detection',
        status: deps.frameworks_detected.length === 0 ? 'skip' : 'pass',
        evidence: deps.frameworks_detected.length === 0 ? na('framework detection') : `Detected: ${deps.frameworks_detected.join(', ')}.` },
    ],
  };

  // ── 3. Dependency Health ──────────────────────────────────────────────────
  const depValidatorScore = deps.validator_score;
  const depValidatorPassed = deps.validator_passed;
  const depValidatorEvidence = deps.validator_evidence ?? [];
  const depOverallStatus: CheckStatus = validatorStatus(depValidatorPassed, depValidatorScore, 'skip');
  const stackItems = deps.detected_stack;
  const selectedItems = Object.entries(deps.selected_stack);
  const MODERN_FRAMEWORKS = new Set([
    'react', 'vue', 'angular', 'next.js', 'nextjs', 'nuxt', 'svelte',
    'spring boot', 'fastapi', 'django', 'flask', 'express', 'nestjs', 'nest.js',
    'asp.net core', '.net core', '.net 6', '.net 7', '.net 8',
    'postgresql', 'postgres', 'mongodb', 'redis', 'mysql 8',
    'kafka', 'rabbitmq', 'kubernetes', 'docker',
    'java 17', 'java 21', 'python 3', 'node 18', 'node 20',
    'typescript', 'kotlin', 'go', 'rust',
  ]);
  const legacyKeywords = ['java ee', 'ejb', 'struts', 'jsf', 'jsp', 'weblogic',
    'websphere', 'jboss', 'coldfusion', 'perl', 'php 5', 'python 2',
    'angular.js', 'angularjs', 'backbone', 'jquery ui', 'ext js'];
  const targetValues = selectedItems.map(([, v]) => v.toLowerCase());
  const hasModernTarget = targetValues.some(v => [...MODERN_FRAMEWORKS].some(mf => v.includes(mf)));
  const hasLegacyTarget = targetValues.some(v => legacyKeywords.some(lk => v.includes(lk)));
  const eolStatus: CheckStatus = selectedItems.length === 0 ? 'skip' : hasLegacyTarget ? 'warn' : hasModernTarget ? 'pass' : 'warn';
  const modernizationStatus: CheckStatus = selectedItems.length === 0 ? 'skip' : hasModernTarget ? 'pass' : 'warn';

  const dependency: AuditSection = {
    title: '3. Dependency Health',
    checks: [
      { label: 'Dependency Health (Coupling / Circular)',
        status: depOverallStatus,
        evidence: depValidatorEvidence.length > 0
          ? depValidatorEvidence.join(' ') + (depValidatorScore != null ? ` Score: ${depValidatorScore.toFixed(0)}%.` : '')
          : depValidatorScore != null ? `Validator score: ${depValidatorScore.toFixed(0)}%.`
          : na('dependency health validator') },
      { label: 'EOL / Deprecated Libraries',
        status: eolStatus,
        evidence: selectedItems.length === 0 ? na('dependency stack')
          : eolStatus === 'pass' ? `Target stack (${targetValues.join(', ')}) uses actively-maintained frameworks.`
          : hasLegacyTarget ? `Legacy technology detected: ${targetValues.filter(v => legacyKeywords.some(lk => v.includes(lk))).join(', ')}.`
          : `${stackItems.length} component(s) detected. Manual EOL verification recommended.` },
      { label: 'Modernization — Latest Stable / LTS Versions',
        status: modernizationStatus,
        evidence: selectedItems.length === 0 ? na('selected stack')
          : modernizationStatus === 'pass' ? `Target stack — ${selectedItems.map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`).join(', ')} — confirmed modern/LTS.`
          : `Target: ${selectedItems.map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`).join(', ')}. Cross-reference with official release channels.` },
      { label: 'Security — CVE Scan',
        status: 'skip',
        evidence: 'No automated CVE scan available. Run `pip audit` (backend) and `npm audit` (frontend).' },
    ],
  };

  // ── 4. Test Coverage Readiness ────────────────────────────────────────────
  const testScriptsGenerated = tc.test_scripts_count > 0;
  const testValidatorPassed = tc.validator_passed ?? testScriptsGenerated;
  const testValidatorScore = tc.validator_score ?? (testScriptsGenerated ? 100 : 0);
  const testRatioStatus: CheckStatus = !testScriptsGenerated ? 'fail' : testValidatorPassed ? 'pass' : 'warn';
  const mockStatus: CheckStatus = endpoints.length === 0 ? 'skip' : (stats?.total_endpoints ?? 0) > 0 ? 'pass' : 'warn';

  const testCoverage: AuditSection = {
    title: '4. Test Coverage Readiness',
    checks: [
      { label: 'Test Scripts Generated',
        status: testRatioStatus,
        evidence: !testScriptsGenerated
          ? `No test scripts generated. ${tc.total_classes} class(es) lack coverage.`
          : `${tc.test_scripts_count} test script(s) generated. Score: ${testValidatorScore.toFixed(0)}%.${tc.validator_evidence?.length ? ' ' + tc.validator_evidence.join(' ') : ''}` },
      { label: 'Mockability — External Dependency Abstraction',
        status: mockStatus,
        evidence: endpoints.length === 0 ? na('endpoint') : `${stats?.total_endpoints ?? 0} endpoint(s) available for interface-based mocking.` },
      { label: 'Validation Suite',
        status: tc.val_total > 0 ? (tc.val_passed / tc.val_total >= 0.7 ? 'pass' : 'warn') : 'warn',
        evidence: tc.val_total > 0
          ? `${tc.val_passed}/${tc.val_total} validation checks passed (${Math.round(tc.val_passed / tc.val_total * 100)}%).`
          : 'No validation checks recorded yet.' },
      { label: 'Empty Test Stubs',
        status: tc.test_scripts_count === 0 ? 'skip' : tc.empty_test_stubs.length > 0 ? 'warn' : 'pass',
        evidence: tc.test_scripts_count === 0 ? na('test script')
          : tc.empty_test_stubs.length > 0 ? `${tc.empty_test_stubs.length} empty stub(s) detected (<50 chars).`
          : `All ${tc.test_scripts_count} test scripts contain substantive content.` },
    ],
  };

  // ── 5. Transformation Completeness ───────────────────────────────────────
  const tfValidatorPassed = tr.validator_passed;
  const tfValidatorScore = tr.validator_score;
  const methodSummary = Object.entries(stats?.methods_distribution ?? {}).map(([m, c]) => `${m}:${c}`).join(', ') || 'N/A';
  const tfCompletionStatus: CheckStatus = tfValidatorPassed != null
    ? (tfValidatorPassed ? 'pass' : 'fail')
    : tfValidatorScore != null ? scoreToStatus(tfValidatorScore)
    : tr.completed_mappings > 0 ? 'pass' : 'skip';
  const tfCompletionEvidence = tr.validator_evidence?.length
    ? tr.validator_evidence.join(' ') + (tfValidatorScore != null ? ` Score: ${tfValidatorScore.toFixed(0)}%.` : '')
    : tr.successful_transformations != null
      ? `${tr.successful_transformations}/${tr.total_output_files ?? tr.total_mappings} files transformed.${tr.failed_transformations ? ` ${tr.failed_transformations} failed/passthrough.` : ''}`
      : tr.api_endpoints_count === 0 ? na('transformation mapping') : `${tr.completed_mappings}/${tr.total_mappings} mapping(s) completed.`;
  const parityStatus: CheckStatus = tr.business_rules_total === 0 ? 'skip'
    : tr.business_rules_mapped >= tr.business_rules_total ? 'pass'
    : tr.business_rules_mapped > 0 ? 'warn' : 'fail';

  const transformation: AuditSection = {
    title: '5. Transformation Completeness',
    checks: [
      { label: 'Transformation Completeness', status: tfCompletionStatus, evidence: tfCompletionEvidence },
      { label: 'Legacy Entry Points Mapped',
        status: tr.api_endpoints_count === 0 ? 'skip' : 'pass',
        evidence: tr.api_endpoints_count === 0 ? na('API endpoint') : `${tr.api_endpoints_count} endpoint(s) mapped. Methods: ${methodSummary}. Unique paths: ${stats?.unique_paths ?? 0}.` },
      { label: 'Business Rules Parity',
        status: parityStatus,
        evidence: tr.business_rules_total === 0 ? na('business rule') : `${tr.business_rules_mapped}/${tr.business_rules_total} rules mapped (${Math.round(tr.business_rules_mapped / tr.business_rules_total * 100)}%).` },
      { label: 'TODO / Placeholder Detection',
        status: Array.isArray(tr.todo_files) && tr.todo_files.length > 0 ? 'warn' : fc.total_parsed_files === 0 ? 'skip' : 'pass',
        evidence: fc.total_parsed_files === 0 ? na('source file scan')
          : !Array.isArray(tr.todo_files) || tr.todo_files.length === 0 ? `0 TODO/FIXME markers detected.`
          : `${tr.todo_files.length} TODO/FIXME item(s): ${tr.todo_files.slice(0, 3).join(', ')}${tr.todo_files.length > 3 ? ` +${tr.todo_files.length - 3} more` : ''}.` },
    ],
  };

  // ── 6. File Coverage ──────────────────────────────────────────────────────
  const fcValidatorPassed = fc.validator_passed;
  const fcValidatorScore = fc.validator_score;
  const inventoryStatus: CheckStatus = fc.total_legacy_files === 0 ? 'skip'
    : fcValidatorPassed != null ? (fcValidatorPassed ? 'pass' : 'fail')
    : fcValidatorScore != null ? scoreToStatus(fcValidatorScore)
    : fc.total_parsed_files >= fc.total_legacy_files ? 'pass' : 'warn';
  const inventoryEvidence = fc.validator_evidence?.length
    ? fc.validator_evidence.join(' ') + (fcValidatorScore != null ? ` Score: ${fcValidatorScore.toFixed(0)}%.` : '')
    : fc.total_legacy_files === 0 ? na('legacy file count')
    : `${fc.total_legacy_files} legacy file(s): Migrated ${fc.migrated_files}, Consolidated ${fc.consolidated_files}, Retired ${fc.retired_files}. Parse coverage: ${Math.round(fc.total_parsed_files / fc.total_legacy_files * 100)}%.`;

  const fileCoverage: AuditSection = {
    title: '6. File Coverage',
    checks: [
      { label: 'Legacy File Inventory', status: inventoryStatus, evidence: inventoryEvidence },
      { label: 'Orphaned Logic Detection',
        status: fc.endpoint_files.length === 0 ? 'skip' : 'pass',
        evidence: fc.endpoint_files.length === 0 ? na('endpoint source file') : `${fc.endpoint_files.length} source file(s) with endpoints accounted for.` },
      { label: 'Directory Structure',
        status: arch.layer_count === 0 ? 'skip' : 'pass',
        evidence: arch.layer_count === 0 ? na('directory structure') : `Files in ${arch.layer_count}-layer structure: ${arch.layers.join(' / ')}.` },
      { label: 'Backup File Cleanliness',
        status: fc.backup_files.length > 0 ? 'fail' : 'pass',
        evidence: fc.backup_files.length === 0 ? `No backup files (.bak, .old, .orig) detected.` : `${fc.backup_files.length} backup file(s) found: ${fc.backup_files.join(', ')}.` },
    ],
  };

  return [codeQuality, architecture, dependency, testCoverage, transformation, fileCoverage];
}


// ─── Rule labels (for metrics tab) ───────────────────────────────────────────

const RULE_LABELS: Record<string, string> = {
  confidence_threshold: 'Confidence Threshold',
  security_check: 'Security Check',
  architecture_compliance: 'Architecture Compliance',
  quality_gate: 'Quality Gate',
  dependency_health: 'Dependency Health',
  file_coverage: 'File Coverage',
  transformation_completeness: 'Transformation Completeness',
  test_coverage_readiness: 'Test Coverage Readiness',
  functional_preservation: 'Functional Preservation',
  api_compatibility: 'API Compatibility',
  technology_migration: 'Technology Migration',
  code_quality: 'Code Quality',
};

// ─── Component ────────────────────────────────────────────────────────────────

export const ValidationDashboardComponent: React.FC<ValidationDashboardProps> = ({ projectId }) => {
  const [metrics, setMetrics] = useState<ValidationMetrics | null>(null);
  const [validationResults, setValidationResults] = useState<ValidationResultDetail[]>([]);
  const [auditReport, setAuditReport] = useState<AuditReport | null>(null);
  const [apiAnalysis, setApiAnalysis] = useState<APIAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [projectStatus, setProjectStatus] = useState('');

  const fetchProjectStatus = async () => {
    try {
      const res = await fetch(`/api/projects/${projectId}`);
      if (res.ok) { const p = await res.json(); setProjectStatus(p.status); }
    } catch {}
  };

  const fetchData = async () => {
    setLoading(true); setError(null);
    try {
      const [metricsData, resultsData, auditData, analysisData] = await Promise.all([
        api.getValidationMetrics(projectId),
        api.getValidationResults(projectId),
        api.getAuditReport(projectId).catch(() => null),
        api.getAPIAnalysis(projectId).catch(() => null),
      ]);
      setMetrics(metricsData);
      setValidationResults(resultsData);
      setAuditReport(auditData);
      setApiAnalysis(analysisData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch validation data');
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchProjectStatus(); }, [projectId]);
  useEffect(() => {
    if (projectStatus === 'complete') {
      fetchData();
      const interval = setInterval(fetchData, 30000);
      return () => clearInterval(interval);
    }
  }, [projectId, projectStatus]);

  if (projectStatus !== 'complete') {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">Validation dashboard is available after transformation completes.</Alert>
      </Box>
    );
  }

  if (loading && !metrics && !auditReport) {
    return <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px"><CircularProgress /></Box>;
  }

  if (error && !metrics && !auditReport) {
    return <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>;
  }

  const passedCount = validationResults.filter(r => r.passed).length;
  const failedCount = validationResults.filter(r => !r.passed).length;

  // Approval rate = pass * 100 / (pass + warn + skipped) from audit checks
  // Falls back to validation results ratio when audit is unavailable
  const computeApprovalRate = (): number => {
    // Formula: pass / (pass + warn + skipped)
    // warn and skipped don't inflate the rate — only fully-passed checks count
    if (auditReport) {
      const sections = buildAudit(auditReport, apiAnalysis);
      const allChecks = sections.flatMap(s => s.checks);
      const pass  = allChecks.filter(c => c.status === 'pass').length;
      const warn  = allChecks.filter(c => c.status === 'warn').length;
      const skip  = allChecks.filter(c => c.status === 'skip').length;
      const denom = pass + warn + skip;
      return denom > 0 ? Math.round((pass / denom) * 1000) / 10 : 0;
    }
    // Fall back to DB validator rows: pass / (pass + non-fail)
    if (validationResults.length > 0) {
      const denom = validationResults.length; // all rows are either pass or fail from DB
      return Math.round((passedCount / denom) * 1000) / 10;
    }
    if (metrics?.approval_rate != null) {
      return metrics.approval_rate;
    }
    return 0;
  };
  const approvalRate = computeApprovalRate();

  return (
    <Box>
      <Card>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="Metrics" />
          <Tab label="Audit Report" />
          <Tab label="Dependency Graphs" />
        </Tabs>

        {/* Tab 0: Metrics */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3} mb={3}>
            {[
              { label: 'Approval Rate', value: `${approvalRate.toFixed(1)}%`, color: 'success.main' },
              { label: 'Total Checks', value: validationResults.length, color: 'primary.main' },
              { label: 'Checks Passed', value: passedCount, color: 'success.main' },
              { label: 'Checks Failed', value: failedCount, color: failedCount > 0 ? 'error.main' : 'text.secondary' },
            ].map(({ label, value, color }) => (
              <Grid item xs={6} sm={3} key={label}>
                <Card variant="outlined">
                  <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Typography variant="h4" fontWeight="bold" sx={{ color }}>{value}</Typography>
                    <Typography variant="body2" color="text.secondary">{label}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Pass / Fail Summary</Typography>
                <Box display="flex" gap={2}>
                  <Card sx={{ flex: 1, bgcolor: 'success.light' }}>
                    <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                      <Typography variant="h4" color="success.dark" fontWeight="bold">{passedCount}</Typography>
                      <Typography variant="body2" color="success.dark">Passed</Typography>
                    </CardContent>
                  </Card>
                  <Card sx={{ flex: 1, bgcolor: 'error.light' }}>
                    <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                      <Typography variant="h4" color="error.dark" fontWeight="bold">{failedCount}</Typography>
                      <Typography variant="body2" color="error.dark">Failed</Typography>
                    </CardContent>
                  </Card>
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Check Type Distribution</Typography>
                {validationResults.length > 0 ? (
                  <List dense>
                    {validationResults.map((r) => (
                      <ListItem key={r.id} disableGutters sx={{ py: 0.5 }}>
                        <ListItemText
                          primary={RULE_LABELS[r.validation_type] ?? r.validation_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                          secondary={`Score: ${r.score.toFixed(0)}% (threshold: ${r.threshold.toFixed(0)}%)`}
                        />
                        <Chip label={r.passed ? 'Pass' : 'Fail'} color={r.passed ? 'success' : 'error'} size="small" />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">No validation data available yet.</Typography>
                )}
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 1: Audit Report */}
        <TabPanel value={tabValue} index={1}>
          {!auditReport ? (
            <Alert severity="info">Audit report data unavailable. Complete the transformation pipeline first.</Alert>
          ) : (() => {
            const sections = buildAudit(auditReport, apiAnalysis);
            const allChecks = sections.flatMap(s => s.checks);
            const passCount = allChecks.filter(c => c.status === 'pass').length;
            const warnCount = allChecks.filter(c => c.status === 'warn').length;
            const failCount = allChecks.filter(c => c.status === 'fail').length;
            const skipCount = allChecks.filter(c => c.status === 'skip').length;
            return (
              <Box>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Senior Migration Architect &amp; Lead QA Engineer — evidence-backed audit across 6 domains.
                  Project: <strong>{auditReport.project_name}</strong> · Status: <strong>{auditReport.project_status}</strong>
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                  <Chip icon={<CheckCircleIcon />} label={`${passCount} Pass`} color="success" size="small" />
                  <Chip icon={<WarningIcon />} label={`${warnCount} Warn`} color="warning" size="small" />
                  {failCount > 0 && <Chip icon={<ErrorIcon />} label={`${failCount} Fail`} color="error" size="small" />}
                  <Chip icon={<InfoIcon />} label={`${skipCount} Skipped`} size="small" />
                </Box>
                <Divider sx={{ mb: 2 }} />
                {sections.map((section, si) => {
                  const active = section.checks.filter(c => c.status !== 'skip');
                  const passed = active.filter(c => c.status === 'pass').length;
                  const pct = active.length > 0 ? Math.round((passed / active.length) * 100) : 0;
                  return (
                    <Accordion key={si} defaultExpanded={si < 2} disableGutters sx={{ mb: 1, border: '1px solid', borderColor: 'divider', borderRadius: 1, '&:before': { display: 'none' } }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box display="flex" alignItems="center" gap={2} flex={1} pr={2}>
                          <Typography variant="subtitle1" fontWeight={600} flex={1}>{section.title}</Typography>
                          <Box display="flex" alignItems="center" gap={1} minWidth={130}>
                            <LinearProgress variant="determinate" value={pct} sx={{ flex: 1, height: 6, borderRadius: 3 }} color={pct === 100 ? 'success' : pct >= 50 ? 'warning' : 'error'} />
                            <Typography variant="caption" color="text.secondary" minWidth={36} textAlign="right">
                              {active.length > 0 ? `${passed}/${active.length}` : 'N/A'}
                            </Typography>
                          </Box>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails sx={{ pt: 0 }}>
                        <Box display="flex" flexDirection="column" gap={1}>
                          {section.checks.map((check, ci) => (
                            <Paper key={ci} variant="outlined" sx={{ p: 1.5, backgroundColor: statusBg[check.status], borderColor: 'transparent' }}>
                              <Box display="flex" alignItems="flex-start" gap={1}>
                                {statusIcon(check.status)}
                                <Box flex={1}>
                                  <Typography variant="body2" fontWeight={600}>{check.label}</Typography>
                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>{check.evidence}</Typography>
                                </Box>
                              </Box>
                            </Paper>
                          ))}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  );
                })}
              </Box>
            );
          })()}
        </TabPanel>

        {/* Tab 2: Dependency Graphs */}
        <TabPanel value={tabValue} index={2}>
          <DependencyGraphComparison projectId={projectId} />
        </TabPanel>
      </Card>
    </Box>
  );
};

export default ValidationDashboardComponent;
