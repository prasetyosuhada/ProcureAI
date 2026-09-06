export type StageStatus = 'pending' | 'in_progress' | 'complete' | 'blocked' | 'not_required';

export type RecommendationStatus = 'none' | 'pending_review' | 'accepted' | 'modified' | 'kept_original' | 'rejected';
export type RequestOutcome = 'open' | 'purchase_submitted' | 'resolved_without_purchase' | 'rejected';
export type ResolutionProvenance = 'demand_analysis' | 'user_override';

export interface RequestProgress {
  clarification: StageStatus;
  demand_analysis: StageStatus;
  validation: StageStatus;
  ready_for_submission: StageStatus;
}

export interface PRSpecification {
  field_name: string;
  value?: string | null;
  is_confirmed: boolean;
}

export interface PRArtifact {
  pr_number?: string | null;
  item_name?: string | null;
  category?: string | null;
  quantity?: number | null;
  department?: string | null;
  cost_center?: string | null;
  purpose?: string | null;
  required_date?: string | null;
  specifications: PRSpecification[];
  status: string;
  is_ready_for_confirmation?: boolean;
}

export interface DemandBreakdown {
  requested_qty: number;
  existing_inventory: number;
  assignable_assets: number;
  reserved_qty: number;
  net_new_purchase: number;
  estimated_saving?: number | null;
  justification?: string | null;
  is_manually_overridden: boolean;
  override_reason?: string | null;
}

export interface AgentAction {
  tool_name: string;
  label: string;
  status: 'running' | 'done' | 'failed';
  result_summary?: string | null;
}

export interface TransientActivity extends AgentAction {
  id: string;
}

export interface AttentionItem {
  id: string;
  category: 'specification' | 'budget' | 'policy';
  severity: 'warning' | 'blocking';
  message: string;
  resolved: boolean;
}

export interface RequestStateResponse {
  thread_id: string;
  pr: PRArtifact;
  progress: RequestProgress;
  demand?: DemandBreakdown | null;
  agent_activity: AgentAction[];
  attention_items: AttentionItem[];
  recommendation_status: RecommendationStatus;
  request_outcome: RequestOutcome;
  resolution_provenance?: ResolutionProvenance | null;
  resolution_reason?: string | null;
  resolved_at?: string | null;
  messages: Array<{
    role: 'user' | 'assistant' | 'system';
    content: string;
  }>;
  last_message?: string | null;
  next_agent: string;
}

export interface RecommendationModificationPayload {
  net_new_purchase?: number;
  user_notes?: string;
}

export interface RecommendationActionPayload {
  action: 'accept' | 'keep_original' | 'modify' | 'reject';
  modification?: RecommendationModificationPayload;
}
