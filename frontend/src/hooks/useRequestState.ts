import { useState, useEffect, useCallback } from 'react';
import { RequestStateResponse } from '../types/requests';
import { UserContext } from '../types/chat';
import { requestsApi } from '../api/requestsApi';

interface UseRequestStateReturn {
  state: RequestStateResponse | null;
  isLoading: boolean;
  error: string | null;
  refreshState: () => Promise<RequestStateResponse | null>;
}

export function useRequestState(
  threadId: string,
  userContext?: UserContext
): UseRequestStateReturn {
  const [state, setState] = useState<RequestStateResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshState = useCallback(async (): Promise<RequestStateResponse | null> => {
    if (!threadId) return null;
    setIsLoading(true);
    setError(null);
    try {
      const data = await requestsApi.getState(threadId, userContext);
      setState(data);
      return data;
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to fetch request state';
      console.error('Error hydrating request state:', err);
      setError(msg);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [threadId, userContext]);

  useEffect(() => {
    refreshState();
  }, [refreshState]);

  return {
    state,
    isLoading,
    error,
    refreshState,
  };
}
