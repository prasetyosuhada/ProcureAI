export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  agentName?: string;
}

export interface RequirementDraft {
  item?: string;
  category?: string;
  quantity?: number;
  purpose?: string;
  required_date?: string;
  specifications?: Record<string, string>;
  is_complete: boolean;
}

export interface DemandAnalysis {
  requested_quantity?: number;
  available_inventory?: number;
  available_assets?: number;
  recommended_quantity?: number;
  justification?: string;
  is_complete: boolean;
}

export interface PRDraft {
  pr_number: string;
  category: string;
  item: string;
  quantity: number;
  specifications?: Record<string, any>;
  purpose: string;
  required_date: string;
  business_justification: string;
  demand_analysis_summary: string;
}

export interface UserContext {
  userId: string;
  userName: string;
  departmentId: string;
  costCenter: string;
}
