import { apiClient } from './client';
import { UserContext } from '../types/chat';
import {
  RequestStateResponse,
  RecommendationActionPayload,
} from '../types/requests';

export interface ConfirmSpecificationsResponse {
  thread_id: string;
  is_confirmed: boolean;
  message: string;
  next_agent: string;
  pr: any;
  progress: any;
  attention_items: any[];
}

export interface ResolveAttentionResponse {
  thread_id: string;
  resolved_item_id: string;
  message: string;
  attention_items: any[];
  blocking_count: number;
}

export interface SubmitPRResponse {
  thread_id: string;
  pr_number: string;
  status: string;
  submitted_at: string;
  message: string;
  pr: any;
  progress: any;
}

function buildHeaders(userContext?: UserContext): Record<string, string> {
  const headers: Record<string, string> = {};
  if (userContext) {
    headers['X-User-ID'] = userContext.userId;
    headers['X-User-Name'] = userContext.userName;
    headers['X-Department-ID'] = userContext.departmentId;
    headers['X-Cost-Center'] = userContext.costCenter;
  }
  return headers;
}

export const requestsApi = {
  /**
   * Fetches the complete state snapshot for a given thread_id.
   * Returns clean initial defaults if thread does not exist yet.
   */
  async getState(threadId: string, userContext?: UserContext): Promise<RequestStateResponse> {
    const response = await apiClient.get<RequestStateResponse>(`/requests/${threadId}/state`, {
      headers: buildHeaders(userContext),
    });
    return response.data;
  },

  /**
   * Explicit action to confirm specifications, triggering transition to Demand Analysis.
   */
  async confirmSpecifications(
    threadId: string,
    userContext?: UserContext
  ): Promise<ConfirmSpecificationsResponse> {
    const response = await apiClient.post<ConfirmSpecificationsResponse>(
      `/requests/${threadId}/confirm-specifications`,
      {},
      { headers: buildHeaders(userContext) }
    );
    return response.data;
  },

  /**
   * Action to accept, modify, or reject AI Demand recommendation (Option A).
   */
  async handleRecommendation(
    threadId: string,
    payload: RecommendationActionPayload,
    userContext?: UserContext
  ): Promise<RequestStateResponse> {
    const response = await apiClient.post<RequestStateResponse>(
      `/requests/${threadId}/recommendation`,
      payload,
      { headers: buildHeaders(userContext) }
    );
    return response.data;
  },

  /**
   * Resolves a flagged attention item.
   */
  async resolveAttentionItem(
    threadId: string,
    itemId: string,
    userContext?: UserContext
  ): Promise<ResolveAttentionResponse> {
    const response = await apiClient.post<ResolveAttentionResponse>(
      `/requests/${threadId}/attention/${itemId}/resolve`,
      {},
      { headers: buildHeaders(userContext) }
    );
    return response.data;
  },

  /**
   * Submits the Purchase Requisition with backend guards check.
   */
  async submitPR(
    threadId: string,
    notes?: string,
    userContext?: UserContext
  ): Promise<SubmitPRResponse> {
    const response = await apiClient.post<SubmitPRResponse>(
      `/requests/${threadId}/submit`,
      { notes },
      { headers: buildHeaders(userContext) }
    );
    return response.data;
  },
};
