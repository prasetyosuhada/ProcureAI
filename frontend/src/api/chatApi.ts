import { apiClient } from './client';
import { UserContext, RequirementDraft, DemandAnalysis, PRDraft } from '../types/chat';

export interface ChatApiRequest {
  thread_id?: string;
  message: string;
  requirement_override?: Record<string, any>;
}

export interface ChatApiResponse {
  thread_id: string;
  message: {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
  };
  requirement_draft?: RequirementDraft | null;
  demand_analysis?: DemandAnalysis | null;
  pr_draft?: PRDraft | null;
  next_agent: 'Clarification' | 'Demand' | 'GeneratePR' | 'Completed' | string;
}

export const chatApi = {
  /**
   * Sends a user message to the LangGraph conversational agent backend.
   */
  async sendMessage(
    payload: ChatApiRequest,
    userContext?: UserContext
  ): Promise<ChatApiResponse> {
    const headers: Record<string, string> = {};
    if (userContext) {
      headers['X-User-ID'] = userContext.userId;
      headers['X-User-Name'] = userContext.userName;
      headers['X-Department-ID'] = userContext.departmentId;
      headers['X-Cost-Center'] = userContext.costCenter;
    }

    const response = await apiClient.post<ChatApiResponse>('/chat', payload, { headers });
    return response.data;
  },

  /**
   * Fetches user context from the backend.
   */
  async getMyContext(): Promise<UserContext> {
    const response = await apiClient.get<any>('/v1/auth/me');
    return {
      userId: response.data.user_id,
      userName: response.data.user_name,
      departmentId: response.data.department_id,
      costCenter: response.data.cost_center,
    };
  },
};
