import React, { useState, useEffect, useMemo, useRef } from 'react';
import { isAxiosError } from 'axios';
import { Navbar } from './components/Navbar';
import { RequestProgressStepper } from './components/RequestProgressStepper';
import { ChatWindow } from './components/ChatWindow';
import { ChatInput } from './components/ChatInput';
import { PRArtifactCard } from './components/PRArtifactCard';
import { DemandAnalysisPanel } from './components/DemandAnalysisPanel';
import { AgentActivityStrip } from './components/AgentActivityStrip';
import { AgentTeamPanel } from './components/AgentTeamPanel';
import { RecommendationCard } from './components/RecommendationCard';
import { AttentionBanner } from './components/AttentionBanner';
import { SubmissionBar } from './components/SubmissionBar';
import { UserContext, ChatMessage } from './types/chat';
import {
  RecommendationActionPayload,
  TransientActivity,
} from './types/requests';
import { useRequestState } from './hooks/useRequestState';
import { chatApi } from './api/chatApi';
import {
  requestsApi,
  ResolveWithoutPurchaseResponse,
  SubmitPRResponse,
} from './api/requestsApi';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ApiErrorResponse {
  detail?: string;
}

function getApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<ApiErrorResponse>(error)) {
    return error.response?.data?.detail || error.message || fallback;
  }
  return error instanceof Error ? error.message : fallback;
}

function getAssistantContextLabel(
  nextAgent?: string,
  requestOutcome?: string
): string {
  if (requestOutcome === 'rejected') return 'Request Paused';
  if (
    requestOutcome === 'purchase_submitted' ||
    requestOutcome === 'resolved_without_purchase' ||
    nextAgent === 'End'
  ) {
    return 'Workflow Complete';
  }

  const labels: Record<string, string> = {
    Clarification: 'Requirement Clarification Agent',
    Demand: 'Demand Analysis Agent',
    GeneratePR: 'Awaiting Human Review',
  };

  return labels[nextAgent || 'Clarification'] || 'ProcureAI Workflow';
}

export const App: React.FC = () => {
  const [threadId, setThreadId] = useState<string>(() => {
    return (
      localStorage.getItem('procureai_thread_id') ||
      `thread_${Math.random().toString(36).substring(2, 10)}`
    );
  });

  const [rawUserContext, setRawUserContext] = useState<UserContext>({
    userId: 'usr_pras',
    userName: 'Prasetyo Suhada',
    departmentId: 'DEPT-ENG',
    costCenter: 'CC-ENG-001',
  });

  // Stabilize userContext reference across renders
  const userContext = useMemo<UserContext>(
    () => ({
      userId: rawUserContext.userId,
      userName: rawUserContext.userName,
      departmentId: rawUserContext.departmentId,
      costCenter: rawUserContext.costCenter,
    }),
    [
      rawUserContext.userId,
      rawUserContext.userName,
      rawUserContext.departmentId,
      rawUserContext.costCenter,
    ]
  );

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [isConfirming, setIsConfirming] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [processingRecommendation, setProcessingRecommendation] = useState<
    RecommendationActionPayload['action'] | null
  >(null);
  const [resolvingAttentionId, setResolvingAttentionId] = useState<
    string | null
  >(null);
  const [isFinalizing, setIsFinalizing] = useState<boolean>(false);
  const [finalizationError, setFinalizationError] = useState<string | null>(null);
  const [submissionResult, setSubmissionResult] =
    useState<SubmitPRResponse | null>(null);
  const [resolutionResult, setResolutionResult] =
    useState<ResolveWithoutPurchaseResponse | null>(null);
  const [transientActivities, setTransientActivities] = useState<
    TransientActivity[]
  >([]);
  const [activitiesFading, setActivitiesFading] = useState(false);
  const streamAbortRef = useRef<AbortController | null>(null);
  const fadeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const clearTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Phase 1 State Hydration Hook
  const {
    state: requestState,
    isLoading: isStateLoading,
    error: stateError,
    refreshState,
  } = useRequestState(threadId, userContext);

  // Sync threadId to localStorage
  useEffect(() => {
    if (threadId) {
      localStorage.setItem('procureai_thread_id', threadId);
    }
  }, [threadId]);

  // Fetch authenticated UserContext from backend
  useEffect(() => {
    chatApi
      .getMyContext()
      .then((ctx) => setRawUserContext(ctx))
      .catch((err) =>
        console.log('Using default client user context:', err.message)
      );
  }, []);

  // Sync messages from backend state when hydrated
  useEffect(() => {
    if (requestState?.messages && requestState.messages.length > 0) {
      const mapped: ChatMessage[] = requestState.messages.map((m, idx) => ({
        id: `msg_hist_${idx}`,
        role: m.role,
        content: m.content,
        timestamp: new Date().toISOString(),
      }));
      setMessages(mapped);
    }
  }, [requestState?.messages]);

  useEffect(
    () => () => {
      streamAbortRef.current?.abort();
      if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);
      if (clearTimerRef.current) clearTimeout(clearTimerRef.current);
    },
    []
  );

  const clearActivityTimers = () => {
    if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);
    if (clearTimerRef.current) clearTimeout(clearTimerRef.current);
    fadeTimerRef.current = null;
    clearTimerRef.current = null;
  };

  const beginActivityStream = () => {
    streamAbortRef.current?.abort();
    clearActivityTimers();
    setTransientActivities([]);
    setActivitiesFading(false);
    const controller = new AbortController();
    streamAbortRef.current = controller;
    return controller;
  };

  const handleStreamActivity = (activity: TransientActivity) => {
    setTransientActivities((current) => {
      const index = current.findIndex((item) => item.id === activity.id);
      if (index === -1) return [...current, activity];
      return current.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...activity } : item
      );
    });
  };

  const scheduleActivityFade = () => {
    clearActivityTimers();
    fadeTimerRef.current = setTimeout(() => setActivitiesFading(true), 700);
    clearTimerRef.current = setTimeout(() => {
      setTransientActivities([]);
      setActivitiesFading(false);
    }, 1_200);
  };

  const markRunningActivitiesFailed = () => {
    setTransientActivities((current) =>
      current.map((activity) =>
        activity.status === 'running'
          ? {
              ...activity,
              status: 'failed',
              result_summary: 'The operation could not be completed.',
            }
          : activity
      )
    );
  };

  const isAbortError = (error: unknown) =>
    error instanceof DOMException && error.name === 'AbortError';

  const handleResetThread = () => {
    streamAbortRef.current?.abort();
    streamAbortRef.current = null;
    clearActivityTimers();
    const newThread = `thread_${Math.random().toString(36).substring(2, 10)}`;
    setThreadId(newThread);
    setMessages([]);
    setErrorMessage(null);
    setProcessingRecommendation(null);
    setResolvingAttentionId(null);
    setFinalizationError(null);
    setSubmissionResult(null);
    setResolutionResult(null);
    setTransientActivities([]);
    setActivitiesFading(false);
  };

  const handleSendMessage = async (
    content: string,
    requirementOverride?: Record<string, unknown>
  ) => {
    setErrorMessage(null);
    const userMsg: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);
    const controller = beginActivityStream();

    try {
      const response = await chatApi.streamMessage(
        {
          thread_id: threadId,
          message: content,
          requirement_override: requirementOverride,
        },
        userContext,
        {
          signal: controller.signal,
          onActivity: handleStreamActivity,
        }
      );

      if (response.message) {
        const aiMsg: ChatMessage = {
          id: `msg_${Date.now()}_ai`,
          role: response.message.role,
          content: response.message.content,
          timestamp: response.message.timestamp || new Date().toISOString(),
        };
        setMessages((prev) => [...prev, aiMsg]);
      }

      // Re-fetch backend state snapshot to rehydrate all components
      await refreshState();
      scheduleActivityFade();
    } catch (err: unknown) {
      if (isAbortError(err)) return;
      console.error('Failed to send message:', err);
      markRunningActivitiesFailed();
      setErrorMessage(getApiErrorMessage(err, 'Failed to send message'));
    } finally {
      if (streamAbortRef.current === controller) {
        streamAbortRef.current = null;
      }
      setIsSending(false);
    }
  };

  const handleConfirmSpecifications = async () => {
    setErrorMessage(null);
    setIsConfirming(true);
    const controller = beginActivityStream();

    try {
      const result = await requestsApi.streamConfirmSpecifications(
        threadId,
        userContext,
        {
          signal: controller.signal,
          onActivity: handleStreamActivity,
        }
      );

      if (result.message) {
        const aiMsg: ChatMessage = {
          id: `msg_${Date.now()}_confirm_res`,
          role: 'assistant',
          content: result.message,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, aiMsg]);
      }

      // Rehydrate full state
      await refreshState();
      scheduleActivityFade();
    } catch (err: unknown) {
      if (isAbortError(err)) return;
      console.error('Failed to confirm specifications:', err);
      markRunningActivitiesFailed();
      setErrorMessage(
        getApiErrorMessage(err, 'Failed to confirm specifications')
      );
    } finally {
      if (streamAbortRef.current === controller) {
        streamAbortRef.current = null;
      }
      setIsConfirming(false);
    }
  };

  const handleRecommendationAction = async (
    payload: RecommendationActionPayload
  ) => {
    setErrorMessage(null);
    setFinalizationError(null);
    setProcessingRecommendation(payload.action);

    try {
      await requestsApi.handleRecommendation(threadId, payload, userContext);
      await refreshState();
      return true;
    } catch (err: unknown) {
      console.error('Failed to process recommendation:', err);
      setErrorMessage(
        getApiErrorMessage(err, 'Failed to process recommendation')
      );
      return false;
    } finally {
      setProcessingRecommendation(null);
    }
  };

  const handleResolveAttention = async (itemId: string) => {
    setErrorMessage(null);
    setResolvingAttentionId(itemId);

    try {
      await requestsApi.resolveAttentionItem(threadId, itemId, userContext);
      await refreshState();
    } catch (err: unknown) {
      console.error('Failed to resolve attention item:', err);
      setErrorMessage(
        getApiErrorMessage(err, 'Failed to resolve attention item')
      );
    } finally {
      setResolvingAttentionId(null);
    }
  };

  const handleSubmitPR = async () => {
    setFinalizationError(null);
    setIsFinalizing(true);

    try {
      const result = await requestsApi.submitPR(
        threadId,
        undefined,
        userContext
      );
      setSubmissionResult(result);
      await refreshState();
    } catch (err: unknown) {
      console.error('Failed to submit PR:', err);
      setFinalizationError(
        getApiErrorMessage(err, 'Failed to submit Purchase Requisition')
      );
    } finally {
      setIsFinalizing(false);
    }
  };

  const handleResolveWithoutPurchase = async () => {
    setFinalizationError(null);
    setIsFinalizing(true);

    try {
      const result = await requestsApi.resolveWithoutPurchase(
        threadId,
        userContext
      );
      setResolutionResult(result);
      await refreshState();
    } catch (err: unknown) {
      console.error('Failed to resolve request without purchase:', err);
      setFinalizationError(
        getApiErrorMessage(err, 'Failed to complete request without purchase')
      );
    } finally {
      setIsFinalizing(false);
    }
  };

  // Safe optional chaining across entire chain
  const currentPhase =
    requestState?.next_agent === 'Demand'
      ? 'Demand'
      : requestState?.progress?.ready_for_submission === 'complete' ||
        requestState?.progress?.ready_for_submission === 'not_required'
      ? 'Completed'
      : requestState?.progress?.clarification === 'complete'
      ? 'GeneratePR'
      : 'Clarification';

  // Condition to display [Confirm Specifications] action prompt (Single Source of Truth from backend)
  const showConfirmPrompt = Boolean(
    requestState?.progress?.clarification !== 'complete' &&
      requestState?.pr?.is_ready_for_confirmation
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* 1. Top Navbar */}
      <Navbar
        userContext={userContext}
        currentPhase={currentPhase}
        threadId={threadId}
        onResetThread={handleResetThread}
      />

      {/* 2. Main Container with Progress Stepper */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col gap-4">
        {/* Progress Stepper */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Procurement Workflow Status
            </span>
            <button
              onClick={() => refreshState()}
              disabled={isStateLoading}
              className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
              title="Sync latest state snapshot from backend"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${
                  isStateLoading ? 'animate-spin' : ''
                }`}
              />
              <span>{isStateLoading ? 'Syncing...' : 'Sync State'}</span>
            </button>
          </div>
          <RequestProgressStepper
            progress={requestState?.progress}
            isLoading={isStateLoading}
            error={stateError}
            onRetry={refreshState}
          />
        </div>

        {/* Global Error Banner */}
        {errorMessage && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between animate-fade-in">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-400 hover:text-rose-200 font-bold px-1"
            >
              ×
            </button>
          </div>
        )}

        <AttentionBanner
          items={requestState?.attention_items}
          resolvingItemId={resolvingAttentionId}
          onResolve={handleResolveAttention}
        />

        {/* 3. Split-Pane Workstation Layout */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[580px] pb-6">
          {/* Left Column: Conversation Pane (Col span: 6/12) */}
          <div className="h-[150vh] min-h-[520px] lg:sticky lg:top-4 lg:col-span-6 lg:h-[calc(100vh-12rem)] lg:min-h-[580px] flex flex-col glass-panel rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl shadow-black/40">
            <div className="shrink-0 p-3.5 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-sm font-semibold text-slate-200">
                  AI Procurement Assistant
                </span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                {getAssistantContextLabel(
                  requestState?.next_agent,
                  requestState?.request_outcome
                )}
              </span>
            </div>

            {/* Chat Conversation View */}
            <div className="min-h-0 flex-1 p-4 flex flex-col">
              <ChatWindow
                messages={messages}
                isLoading={isSending}
                isConfirming={isConfirming}
                prArtifact={requestState?.pr}
                showConfirmPrompt={showConfirmPrompt}
                onConfirmSpecifications={handleConfirmSpecifications}
                transientActivities={transientActivities}
                activitiesFading={activitiesFading}
                activeAgentLabel={
                  requestState?.next_agent === 'Demand'
                    ? 'ProcureAI is analyzing warehouse inventory & assets...'
                    : 'ProcureAI is clarifying requirements...'
                }
              />

              {/* Chat Input */}
              <div className="shrink-0 pt-2">
                <ChatInput
                  onSendMessage={(text) => handleSendMessage(text)}
                  isLoading={isSending || isConfirming}
                  hasMessages={messages.length > 0}
                />
              </div>
            </div>
          </div>

          {/* Right Column: Interactive Artifact Workspace (Col span: 6/12) */}
          <div className="lg:col-span-6 flex flex-col gap-4">
            {/* 1. Agent roster and live ownership */}
            <AgentTeamPanel
              progress={requestState?.progress}
              nextAgent={requestState?.next_agent}
              requestOutcome={requestState?.request_outcome}
              transientActivities={transientActivities}
              isRunActive={isSending || isConfirming}
              activeAgentHint={
                isConfirming
                  ? 'demand'
                  : isSending
                  ? 'clarification'
                  : undefined
              }
            />

            {/* 2. Purchase Requisition Artifact Card */}
            <PRArtifactCard pr={requestState?.pr} />

            {/* 2. Demand & Inventory Optimization Panel */}
            <DemandAnalysisPanel
              demand={requestState?.demand}
              progress={requestState?.progress}
            />

            {/* 3. Explicit Human Decision on AI Recommendation */}
            <RecommendationCard
              demand={requestState?.demand}
              progress={requestState?.progress}
              recommendationStatus={
                requestState?.recommendation_status || 'none'
              }
              processingAction={processingRecommendation}
              onAction={handleRecommendationAction}
            />

            {/* 4. Agent Activity & Execution Telemetry */}
            <AgentActivityStrip activities={requestState?.agent_activity} />

            {/* 5. Final Submission Gate & Confirmation */}
            {requestState?.progress?.demand_analysis === 'complete' && (
              <SubmissionBar
                pr={requestState?.pr}
                attentionItems={requestState?.attention_items}
                recommendationStatus={
                  requestState?.recommendation_status || 'none'
                }
                requestOutcome={requestState?.request_outcome || 'open'}
                isFinalizing={isFinalizing}
                finalizationError={finalizationError}
                submitResult={submissionResult}
                resolutionResult={resolutionResult}
                onSubmit={handleSubmitPR}
                onResolveWithoutPurchase={handleResolveWithoutPurchase}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
