import React, { useState, useEffect, useMemo } from 'react';
import { Navbar } from './components/Navbar';
import { RequestProgressStepper } from './components/RequestProgressStepper';
import { ChatWindow } from './components/ChatWindow';
import { ChatInput } from './components/ChatInput';
import { UserContext, ChatMessage } from './types/chat';
import { useRequestState } from './hooks/useRequestState';
import { chatApi } from './api/chatApi';
import {
  FileText,
  Boxes,
  Activity,
  AlertTriangle,
  RefreshCw,
  Sparkles,
} from 'lucide-react';

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

  // Stabilize userContext reference across renders to prevent infinite fetch loops
  const userContext = useMemo<UserContext>(() => ({
    userId: rawUserContext.userId,
    userName: rawUserContext.userName,
    departmentId: rawUserContext.departmentId,
    costCenter: rawUserContext.costCenter,
  }), [
    rawUserContext.userId,
    rawUserContext.userName,
    rawUserContext.departmentId,
    rawUserContext.costCenter,
  ]);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

  const handleResetThread = () => {
    const newThread = `thread_${Math.random().toString(36).substring(2, 10)}`;
    setThreadId(newThread);
    setMessages([]);
    setErrorMessage(null);
  };

  const handleSendMessage = async (
    content: string,
    requirementOverride?: Record<string, any>
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

    try {
      const response = await chatApi.sendMessage(
        {
          thread_id: threadId,
          message: content,
          requirement_override: requirementOverride,
        },
        userContext
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
    } catch (err: any) {
      console.error('Failed to send message:', err);
      const errMsg =
        err.response?.data?.detail || err.message || 'Failed to send message';
      setErrorMessage(errMsg);
    } finally {
      setIsSending(false);
    }
  };

  const currentPhase =
    requestState?.next_agent === 'Demand'
      ? 'Demand'
      : requestState?.progress.ready_for_submission === 'complete'
      ? 'Completed'
      : requestState?.progress.clarification === 'complete'
      ? 'GeneratePR'
      : 'Clarification';

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
        {/* Progress Stepper (Bind to backend requestState.progress, with explicit loading/error states) */}
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
                className={`w-3.5 h-3.5 ${isStateLoading ? 'animate-spin' : ''}`}
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

        {/* 3. Split-Pane Workstation Layout */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[580px]">
          {/* Left Column: Conversation Pane (Col span: 6/12) */}
          <div className="lg:col-span-6 flex flex-col glass-panel rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl shadow-black/40">
            <div className="p-3.5 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-sm font-semibold text-slate-200">
                  AI Procurement Assistant
                </span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                {requestState?.next_agent || 'Clarification'} Agent
              </span>
            </div>

            {/* Chat Conversation View */}
            <div className="flex-1 overflow-y-auto p-4 flex flex-col justify-between">
              <ChatWindow
                messages={messages}
                isLoading={isSending}
              />

              {/* Chat Input */}
              <div className="pt-2">
                <ChatInput
                  onSendMessage={(text) => handleSendMessage(text)}
                  isLoading={isSending}
                />
              </div>
            </div>
          </div>

          {/* Right Column: Procurement Artifacts & Demand Panel (Col span: 6/12) */}
          <div className="lg:col-span-6 flex flex-col gap-4">
            {/* Header for Artifact Workspace */}
            <div className="glass-panel rounded-2xl border border-slate-800/80 p-5 flex flex-col gap-4 shadow-xl shadow-black/40">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3.5">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-200">
                      Live Procurement Artifacts
                    </h3>
                    <p className="text-xs text-slate-400">
                      Auto-generated PR specifications & demand telemetry
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded-lg border border-slate-700/50">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  <span>
                    {isStateLoading
                      ? 'Syncing State...'
                      : requestState
                      ? 'State Hydrated'
                      : 'Connecting...'}
                  </span>
                </div>
              </div>

              {/* Step 3a: Hydrated State Diagnostics Card */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 flex flex-col gap-1">
                  <span className="text-[11px] text-slate-500 font-medium">
                    PR Item
                  </span>
                  <span className="text-xs font-semibold text-slate-200 truncate">
                    {requestState?.pr?.item_name || '—'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 flex flex-col gap-1">
                  <span className="text-[11px] text-slate-500 font-medium">
                    Qty Requested
                  </span>
                  <span className="text-xs font-semibold text-slate-200">
                    {requestState?.pr?.quantity ?? '—'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 flex flex-col gap-1">
                  <span className="text-[11px] text-slate-500 font-medium">
                    Net Purchase
                  </span>
                  <span className="text-xs font-semibold text-emerald-400">
                    {requestState?.demand?.net_new_purchase ?? '—'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 flex flex-col gap-1">
                  <span className="text-[11px] text-slate-500 font-medium">
                    Attention Flags
                  </span>
                  <span className="text-xs font-semibold text-amber-400">
                    {requestState?.attention_items?.length ?? 0}
                  </span>
                </div>
              </div>

              {/* Placeholder Card: Ready for Step 3c & 3d */}
              <div className="flex flex-col items-center justify-center p-8 rounded-xl border border-dashed border-slate-800 bg-slate-900/40 text-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center text-slate-400">
                  <Boxes className="w-6 h-6 text-indigo-400" />
                </div>
                <div className="flex flex-col gap-1">
                  <h4 className="text-sm font-semibold text-slate-300">
                    Artifact Panel Shell (Step 3a Ready)
                  </h4>
                  <p className="text-xs text-slate-400 max-w-sm">
                    In Step 3c & 3d, this panel will render the interactive{' '}
                    <code className="text-indigo-300 font-mono text-[11px]">
                      PRArtifactCard
                    </code>
                    ,{' '}
                    <code className="text-indigo-300 font-mono text-[11px]">
                      DemandAnalysisPanel
                    </code>
                    ,{' '}
                    <code className="text-indigo-300 font-mono text-[11px]">
                      AttentionBanner
                    </code>
                    , and{' '}
                    <code className="text-indigo-300 font-mono text-[11px]">
                      SubmissionBar
                    </code>
                    .
                  </p>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-slate-500 bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-800">
                  <Activity className="w-3.5 h-3.5 text-blue-400" />
                  <span>
                    Agent Activity telemetry:{' '}
                    {requestState?.agent_activity?.length ?? 0} actions recorded
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
