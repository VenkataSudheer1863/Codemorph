const API_BASE = '/api';

export interface ProjectSummary {
  id: string;
  name: string;
  path: string;
  description: string;
  status: string;
  created_at: string;
  total_files: number;
  total_loc: number;
}

export interface Project {
  id: string;
  name: string;
  path: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
  total_files: number;
  total_loc: number;
  languages_count: number;
  frameworks_count: number;
  language_distribution: Record<string, number> | null;
  architecture_layers: Record<string, LayerData> | null;
  detected_apis: ApiEndpoint[] | null;
  detected_tables: DbTable[] | null;
  detected_stack: StackItem[] | null;
  recommendations: Recommendation[] | null;
  selected_stack: Record<string, string> | null;
  transformation_progress: TransformationProgress | null;
  transformation_mappings: TransformationMapping[] | null;
  project_summary: string;
  test_scripts: TestScript[] | null;
  error_message: string | null;
}

// Enhanced interfaces for new functionality
export interface DatabaseAnalysis {
  schemas: DatabaseSchema[];
  orm_models: Record<string, string>;
  analysis: DatabaseAnalysisMetrics;
  recommendations: DatabaseRecommendation[];
}

export interface DatabaseSchema {
  name: string;
  database_type: string;
  tables: DatabaseTable[];
  views: DatabaseView[];
  procedures: DatabaseProcedure[];
  functions: DatabaseFunction[];
  triggers: DatabaseTrigger[];
}

export interface DatabaseTable {
  name: string;
  columns: DatabaseColumn[];
  primary_keys: string[];
  foreign_keys: ForeignKey[];
  indexes: DatabaseIndex[];
  comment?: string;
  engine?: string;
  charset?: string;
}

export interface DatabaseColumn {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  foreign_key?: string;
  default_value?: string;
  max_length?: number;
  precision?: number;
  scale?: number;
  auto_increment: boolean;
  unique: boolean;
  comment?: string;
}

export interface ForeignKey {
  name: string;
  columns: string[];
  referenced_table: string;
  referenced_columns: string[];
  on_delete: string;
  on_update: string;
}

export interface DatabaseIndex {
  name: string;
  columns: string[];
  unique: boolean;
  type: string;
}

export interface DatabaseView {
  name: string;
  definition: string;
  type: string;
}

export interface DatabaseProcedure {
  name: string;
  parameters: string;
  body: string;
  type: string;
}

export interface DatabaseFunction {
  name: string;
  parameters: string;
  return_type: string;
  body: string;
  type: string;
}

export interface DatabaseTrigger {
  name: string;
  timing: string;
  event: string;
  table: string;
  body: string;
  type: string;
}

export interface DatabaseAnalysisMetrics {
  total_schemas: number;
  total_tables: number;
  total_columns: number;
  total_indexes: number;
  total_foreign_keys: number;
  primary_database_type: string;
  relationship_analysis: RelationshipAnalysis;
  type_analysis: TypeAnalysis;
  complexity_score: number;
}

export interface RelationshipAnalysis {
  total_relationships: number;
  isolated_tables: number;
  highly_connected_tables: number;
  relationship_graph: Record<string, TableRelationships>;
}

export interface TableRelationships {
  references: string[];
  referenced_by: string[];
}

export interface TypeAnalysis {
  type_distribution: Record<string, number>;
  most_common_type: string;
  total_columns: number;
}

export interface DatabaseRecommendation {
  type: string;
  priority: string;
  title: string;
  description: string;
  affected_tables?: string[];
  affected_columns?: string[];
}

export interface APIAnalysis {
  endpoints: APIEndpointDetail[];
  models: APIModel[];
  frameworks: string[];
  openapi_spec: OpenAPISpec;
  statistics: APIStatistics;
  postman_collection: PostmanCollection;
  curl_examples: CurlExample[];
  conversion_summary: ConversionSummary;
}

export interface APIEndpointDetail {
  path: string;
  method: string;
  function_name: string;
  parameters: APIParameter[];
  responses: APIResponse[];
  summary?: string;
  description?: string;
  tags: string[];
  deprecated: boolean;
  security?: string[];
  file_path: string;
  line_number: number;
}

export interface APIParameter {
  name: string;
  type: string;
  required: boolean;
  location: string;
  description?: string;
  default_value?: string;
  validation?: Record<string, any>;
}

export interface APIResponse {
  status_code: number;
  description: string;
  content_type: string;
  schema?: Record<string, any>;
  examples?: Record<string, any>[];
}

export interface APIModel {
  name: string;
  properties: Record<string, Record<string, any>>;
  required_fields: string[];
  description?: string;
  example?: Record<string, any>;
}

export interface OpenAPISpec {
  openapi: string;
  info: OpenAPIInfo;
  paths: Record<string, any>;
  components: OpenAPIComponents;
}

export interface OpenAPIInfo {
  title: string;
  version: string;
  description: string;
}

export interface OpenAPIComponents {
  schemas: Record<string, any>;
}

export interface APIStatistics {
  total_endpoints: number;
  total_models: number;
  methods_distribution: Record<string, number>;
  unique_paths: number;
  parameters_total: number;
  avg_parameters_per_endpoint: number;
}

export interface PostmanCollection {
  info: PostmanInfo;
  item: PostmanItem[];
}

export interface PostmanInfo {
  name: string;
  description: string;
  schema: string;
}

export interface PostmanItem {
  name: string;
  request: PostmanRequest;
}

export interface PostmanRequest {
  method: string;
  header: any[];
  url: PostmanUrl;
  body?: PostmanBody;
}

export interface PostmanUrl {
  raw: string;
  host: string[];
  path: string[];
  query?: PostmanQuery[];
}

export interface PostmanQuery {
  key: string;
  value: string;
  description: string;
}

export interface PostmanBody {
  mode: string;
  raw: string;
  options: PostmanBodyOptions;
}

export interface PostmanBodyOptions {
  raw: PostmanRawOptions;
}

export interface PostmanRawOptions {
  language: string;
}

export interface CurlExample {
  endpoint: string;
  curl: string;
}

export interface ConversionSummary {
  endpoints_converted: number;
  models_extracted: number;
  frameworks_detected: string[];
  openapi_generated: boolean;
  postman_collection_generated: boolean;
  curl_examples_generated: boolean;
}

export interface ValidationResultDetail {
  id: string;
  validation_type: string;
  status: string;
  score: number;
  threshold: number;
  passed: boolean;
  message: string;
  evidence: string[];
  recommendations: string[];
  reviewer?: string;
  created_at?: string;
}

export interface ValidationDashboard {
  pending_reviews: ReviewRequest[];
  pending_count: number;
  priority_distribution: Record<string, number>;
  timed_out_reviews: string[];
  review_history_count: number;
  statistics: ValidationStatistics;
}

export interface ReviewRequest {
  id: string;
  title: string;
  description: string;
  priority: string;
  validation_results: ValidationResult[];
  context_data: Record<string, any>;
  created_at: string;
  expires_at: string;
  assigned_to?: string;
  status: string;
  review_notes?: string;
  decision_reason?: string;
}

export interface ValidationResult {
  rule_type: string;
  status: string;
  score: number;
  threshold: number;
  passed: boolean;
  message: string;
  evidence: string[];
  recommendations: string[];
  timestamp: string;
  reviewer?: string;
  review_notes?: string;
}

export interface ValidationStatistics {
  total_reviews_created: number;
  completed_reviews: number;
  timeout_rate: number;
}

export interface ValidationMetrics {
  total_validations: number;
  passed_validations: number;
  failed_validations: number;
  approval_rate: number;
  average_review_time_minutes: number;
  rule_type_distribution: Record<string, number>;
  priority_distribution: Record<string, number>;
  reviewer_statistics: Record<string, ReviewerStats>;
  current_pending: number;
}

export interface ReviewerStats {
  total: number;
  approved: number;
  rejected: number;
}

export interface ValidationDecision {
  decision: string;
  reviewer: string;
  notes?: string;
  decision_reason?: string;
}

export interface ValidationCriteria {
  rule_type: string;
  threshold: number;
  description: string;
  auto_approve_threshold?: number;
  requires_human_review: boolean;
  timeout_minutes: number;
  escalation_rules?: Record<string, any>;
}

export interface AuditReport {
  project_id: string;
  project_name: string;
  project_path: string;
  project_status: string;
  validation_summary?: {
    total_checks: number;
    passed_checks: number;
    failed_checks: number;
    approval_rate: number;
    checks_by_type: Record<string, {
      score: number;
      threshold: number;
      passed: boolean;
      message: string;
      evidence: string[];
    }>;
  };
  code_quality: {
    avg_complexity: number | null;
    max_complexity: number | null;
    avg_maintainability: number | null;
    total_functions: number;
    total_classes: number;
    total_parsed_files: number;
    successful_parses: number;
    failed_parses: number;
    parse_success_rate: number | null;
    large_files: string[];
    god_class_candidates: string[];
    frameworks_detected: string[];
    total_endpoints: number;
    linting_violations: number;
    style_guide: string;
    validator_score?: number | null;
    validator_passed?: boolean | null;
  };
  architecture: {
    layers: string[];
    architecture_layers: Record<string, any>;
    high_complexity_components: string[];
    total_components: number;
    layer_count: number;
    validator_score?: number | null;
    validator_passed?: boolean | null;
    validator_evidence?: string[];
  };
  dependencies: {
    detected_stack: StackItem[];
    selected_stack: Record<string, string>;
    frameworks_detected: string[];
    validator_score?: number | null;
    validator_passed?: boolean | null;
    validator_evidence?: string[];
  };
  test_coverage: {
    test_scripts_count: number;
    empty_test_stubs: any[];
    total_classes: number;
    val_passed: number;
    val_total: number;
    validator_score?: number | null;
    validator_passed?: boolean | null;
    validator_evidence?: string[];
  };
  transformation: {
    total_mappings: number;
    completed_mappings: number;
    api_endpoints_count: number;
    api_endpoints: any[];
    todo_files: string[] | string[];
    selected_stack: Record<string, string>;
    business_rules_total: number;
    business_rules_mapped: number;
    total_output_files?: number;
    successful_transformations?: number;
    failed_transformations?: number;
    validator_score?: number | null;
    validator_passed?: boolean | null;
    validator_evidence?: string[];
  };
  file_coverage: {
    total_legacy_files: number;
    total_parsed_files: number;
    migrated_files: number;
    consolidated_files: number;
    retired_files: number;
    endpoint_files: string[];
    backup_files: string[];
    large_files: string[];
    validator_score?: number | null;
    validator_passed?: boolean | null;
    validator_evidence?: string[];
  };
}

export interface TestScript {
  name: string;
  type: string;
  framework: string;
  description: string;
  content: string;
  file_name: string;
}

export interface LayerData {
  files: string[];
  components: string[];
  frameworks: string[];
  file_count: number;
}

export interface ApiEndpoint {
  method: string;
  path: string;
  handler: string;
  type: string;
  file: string;
}

export interface DbTable {
  name: string;
  type: string;
  columns: number;
  relationships: number;
  file: string;
}

export interface StackItem {
  category: string;
  label: string;
  detected: string;
  confidence: number;
  alternatives: string[];
}

export interface Recommendation {
  category: string;
  label: string;
  detected: string;
  confidence: number;
  suggestions: string[];
}

export interface TransformationProgress {
  processed: number;
  total: number;
  percent: number;
  current_file?: string;
  current_mapping?: string;
  elapsed_time?: number;
  estimated_remaining?: number;
  completed?: boolean;
}

export interface TransformationMapping {
  source: string;
  target: string;
  file_count: number;
  status: string;
  category: string;
}

export interface PipelineStatus {
  project_id: string;
  status: string;
  stage: string;
  progress: number;
  message: string;
}

export interface ProjectCreate {
  name: string;
  path: string;
  description: string;
}

export interface StackSelection {
  selections: Record<string, string>;
}

export interface DependencyGraphNode {
  id: string;
  name: string;
  type: 'file' | 'class' | 'function' | 'module';
  language?: string;
  file?: string;
  loc?: number;
}

export interface DependencyGraphEdge {
  source: string;
  target: string;
  type: 'import' | 'contains' | 'inheritance' | 'call' | 'circular';
  weight?: number;
}

export interface DependencyGraphCluster {
  name: string;
  members: string[];
}

export interface DependencyGraphMetrics {
  total_nodes: number;
  total_edges: number;
  circular_dependencies: number;
  file_nodes?: number;
  class_nodes?: number;
  function_nodes?: number;
  import_edges?: number;
  contains_edges?: number;
  inheritance_edges?: number;
}

export interface DependencyGraph {
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
  clusters: DependencyGraphCluster[];
  metrics: DependencyGraphMetrics;
  cycles?: string[][];
}

export interface DependencyGraphComparison {
  structure_match_score: number;
  class_match_score: number;
  edge_preservation_rate: number;
  combined_score: number;
  original_metrics: DependencyGraphMetrics;
  converted_metrics: DependencyGraphMetrics;
  nodes_matched: number;
  classes_matched: number;
  nodes_only_in_original: string[];
  nodes_only_in_converted: string[];
  edges_preserved: number;
  edges_removed: number;
  edges_added: number;
  cycles_original: number;
  cycles_converted: number;
  cycles_resolved: number;
  validation_status: 'pass' | 'warn' | 'fail';
}

export interface DependencyGraphsResponse {
  project_id: string;
  initial_graph: DependencyGraph;
  converted_graph: DependencyGraph;
  comparison: DependencyGraphComparison;
  has_converted: boolean;
}

export interface FunctionalPreservationReport {
  project_id: string;
  available: boolean;
  message?: string;
  overall_passed?: boolean;
  overall_score?: number;
  files_checked?: number;
  files_passed?: number;
  files_failed?: number;
  preservation_rate?: number;
  api_preservation_rate?: number;
  api_contract_check?: {
    total_endpoints: number;
    preserved_endpoints: number;
    missing_endpoints: { method: string; path: string; original_file: string }[];
    preservation_rate: number;
    passed: boolean;
  };
  failed_files_summary?: {
    file: string;
    verdict: string;
    missing: string[];
    summary: string;
  }[];
  file_results?: {
    file_path: string;
    passed: boolean;
    score: number;
    verdict: string;
    summary: string;
    preserved_rules: string[];
    missing_rules: string[];
    changed_behaviors: string[];
    verification_method: string;
  }[];
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  listProjects: () => request<ProjectSummary[]>('/projects'),

  getProject: (id: string) => request<Project>(`/projects/${encodeURIComponent(id)}`),

  createProject: (data: ProjectCreate) =>
    request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateProject: (id: string, data: { name?: string; description?: string }) =>
    request<Project>(`/projects/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteProject: (id: string) =>
    request<{ detail: string }>(`/projects/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  startPipeline: (id: string) =>
    request<{ detail: string }>(`/projects/${encodeURIComponent(id)}/start`, { method: 'POST' }),

  getStatus: (id: string) =>
    request<PipelineStatus>(`/projects/${encodeURIComponent(id)}/status`),

  selectStack: (id: string, selections: Record<string, string>) =>
    request<{ detail: string }>(`/projects/${encodeURIComponent(id)}/select-stack`, {
      method: 'POST',
      body: JSON.stringify({ selections }),
    }),

  restartFrom: (id: string, stage: string) =>
    request<{ detail: string }>(`/projects/${encodeURIComponent(id)}/restart-from/${encodeURIComponent(stage)}`, {
      method: 'POST',
    }),

  downloadLegacyReport: (id: string) =>
    `${API_BASE}/projects/${encodeURIComponent(id)}/report/legacy`,

  downloadMigrationReport: (id: string) =>
    `${API_BASE}/projects/${encodeURIComponent(id)}/report/migration`,

  downloadArtifacts: (id: string) =>
    `${API_BASE}/projects/${encodeURIComponent(id)}/artifacts`,

  // Enhanced Analysis APIs
  startDatabaseAnalysis: (id: string) =>
    request<{ message: string; project_id: string; status: string }>(`/enhanced/database-analysis/${encodeURIComponent(id)}`, {
      method: 'POST',
    }),

  getDatabaseAnalysis: (id: string) =>
    request<DatabaseAnalysis>(`/enhanced/database-analysis/${encodeURIComponent(id)}/results`),

  startAPIAnalysis: (id: string) =>
    request<{ message: string; project_id: string; status: string }>(`/enhanced/api-analysis/${encodeURIComponent(id)}`, {
      method: 'POST',
    }),

  getAPIAnalysis: (id: string) =>
    request<APIAnalysis>(`/enhanced/api-analysis/${encodeURIComponent(id)}/results`),

  // Validation APIs
  getValidationResults: (projectId: string) =>
    request<ValidationResultDetail[]>(`/enhanced/validation/results/${encodeURIComponent(projectId)}`),

  getValidationDashboard: (projectId?: string) =>
    request<ValidationDashboard>(`/enhanced/validation/dashboard${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''}`),

  submitReviewDecision: (requestId: string, decision: ValidationDecision) =>
    request<{ success: boolean; message: string; request_id: string; decision: string; reviewer: string }>(`/enhanced/validation/review/${encodeURIComponent(requestId)}`, {
      method: 'POST',
      body: JSON.stringify(decision),
    }),

  getValidationMetrics: (projectId?: string) =>
    request<ValidationMetrics>(`/enhanced/validation/metrics${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''}`),

  configureValidationCriteria: (criteria: ValidationCriteria[]) =>
    request<{ success: boolean; message: string; criteria_count: number }>('/enhanced/validation/configure', {
      method: 'POST',
      body: JSON.stringify({ criteria }),
    }),

  getOrchestratorStatus: (id: string) =>
    request<{
      project_id: string;
      current_step: string;
      completed_steps: string[];
      status: string;
      confidence_scores: Record<string, number>;
      validation_status: string;
    }>(`/enhanced/orchestrator/${encodeURIComponent(id)}/status`),

  getAuditReport: (id: string) =>
    request<import('./api').AuditReport>(`/enhanced/audit/${encodeURIComponent(id)}`),

  getDependencyGraphs: (id: string) =>
    request<DependencyGraphsResponse>(`/enhanced/dependency-graphs/${encodeURIComponent(id)}`),

  getFunctionalPreservation: (id: string) =>
    request<FunctionalPreservationReport>(`/enhanced/functional-preservation/${encodeURIComponent(id)}`),
};
