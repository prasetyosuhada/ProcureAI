import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { ChatWindow } from './components/ChatWindow';
import { ChatInput } from './components/ChatInput';
import { ChatMessage, UserContext, RequirementDraft, DemandAnalysis, PRDraft } from './types/chat';
import { chatApi } from './api/chatApi';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [threadId, setThreadId] = useState<string>(() => {
    return localStorage.getItem('procureai_thread_id') || `thread_${Math.random().toString(36).substring(2, 11)}`;
  });
  const [currentPhase, setCurrentPhase] = useState<'Clarification' | 'Demand' | 'GeneratePR' | 'Completed'>('Clarification');
  const [, setRequirementDraft] = useState<RequirementDraft | null>(null);
  const [, setDemandAnalysis] = useState<DemandAnalysis | null>(null);
  const [, setPrDraft] = useState<PRDraft | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Authenticated user context
  const [userContext, setUserContext] = useState<UserContext>({
    userId: 'usr_pras',
    userName: 'Prasetyo Suhada',
    departmentId: 'DEPT-ENG',
    costCenter: 'CC-ENG-001'
  });

  // Sync thread_id with localStorage
  useEffect(() => {
    if (threadId) {
      localStorage.setItem('procureai_thread_id', threadId);
    }
  }, [threadId]);

  // Optionally fetch backend user info on mount
  useEffect(() => {
    chatApi.getMyContext()
      .then((ctx) => setUserContext(ctx))
      .catch((err) => console.log('Using default client user context:', err.message));
  }, []);

  const handleSendMessage = async (content: string) => {
    setErrorMessage(null);
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await chatApi.sendMessage(
        {
          thread_id: threadId,
          message: content
        },
        userContext
      );

      // Preserve or update thread ID from backend
      if (response.thread_id && response.thread_id !== threadId) {
        setThreadId(response.thread_id);
      }

      // Update Agent workflow state
      if (response.next_agent) {
        if (response.next_agent === 'Demand') {
          setCurrentPhase('Demand');
        } else if (response.next_agent === 'GeneratePR') {
          setCurrentPhase('GeneratePR');
        } else if (response.next_agent === 'Completed') {
          setCurrentPhase('Completed');
        } else {
          setCurrentPhase('Clarification');
        }
      }

      if (response.requirement_draft) setRequirementDraft(response.requirement_draft);
      if (response.demand_analysis) setDemandAnalysis(response.demand_analysis);
      if (response.pr_draft) setPrDraft(response.pr_draft);

      // Append Agent response message
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_ai`,
        role: 'assistant',
        content: response.message.content,
        timestamp: response.message.timestamp || new Date().toISOString(),
        agentName: response.next_agent === 'Demand' || response.next_agent === 'GeneratePR'
          ? 'Demand Analysis Agent'
          : 'Clarification Agent'
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Chat API error:', error);
      const errText = error.response?.data?.detail || error.message || 'Failed to communicate with ProcureAI backend';
      setErrorMessage(errText);

      const errorMessageObj: ChatMessage = {
        id: `msg_${Date.now()}_error`,
        role: 'assistant',
        content: `⚠️ **Connection Error:** ${errText}. Please ensure the FastAPI backend is running on http://localhost:8000.`,
        timestamp: new Date().toISOString(),
        agentName: 'System'
      };
      setMessages((prev) => [...prev, errorMessageObj]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetThread = () => {
    const newThread = `thread_${Math.random().toString(36).substring(2, 11)}`;
    setThreadId(newThread);
    setMessages([]);
    setRequirementDraft(null);
    setDemandAnalysis(null);
    setPrDraft(null);
    setCurrentPhase('Clarification');
    setErrorMessage(null);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar
        userContext={userContext}
        currentPhase={currentPhase}
        threadId={threadId}
        onResetThread={handleResetThread}
      />

      {/* Main Conversation Stream */}
      <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {errorMessage && (
          <div className="bg-rose-500/10 border-b border-rose-500/20 px-4 py-2 text-center text-xs text-rose-400">
            {errorMessage}
          </div>
        )}
        <ChatWindow messages={messages} isLoading={isLoading} />
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </main>
    </div>
  );
};

export default App;
