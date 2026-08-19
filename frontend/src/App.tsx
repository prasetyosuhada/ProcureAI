import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { ChatWindow } from './components/ChatWindow';
import { ChatInput } from './components/ChatInput';
import { PRDraftReviewModal } from './components/PRDraftReviewModal';
import { ChatMessage, UserContext, RequirementDraft, DemandAnalysis, PRDraft } from './types/chat';
import { chatApi } from './api/chatApi';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [threadId, setThreadId] = useState<string>(() => {
    return localStorage.getItem('procureai_thread_id') || `thread_${Math.random().toString(36).substring(2, 11)}`;
  });
  const [currentPhase, setCurrentPhase] = useState<'Clarification' | 'Demand' | 'GeneratePR' | 'Completed'>('Clarification');
  const [requirementDraft, setRequirementDraft] = useState<RequirementDraft | null>(null);
  const [demandAnalysis, setDemandAnalysis] = useState<DemandAnalysis | null>(null);
  const [prDraft, setPrDraft] = useState<PRDraft | null>(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState<boolean>(false);
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

  // Fetch backend user info on mount
  useEffect(() => {
    chatApi.getMyContext()
      .then((ctx) => setUserContext(ctx))
      .catch((err) => console.log('Using default client user context:', err.message));
  }, []);

  const handleSendMessage = async (content: string, requirementOverride?: Record<string, any>) => {
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
          message: content,
          requirement_override: requirementOverride
        },
        userContext
      );

      // Update thread ID if provided
      if (response.thread_id && response.thread_id !== threadId) {
        setThreadId(response.thread_id);
      }

      // Update Agent workflow phase
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

      const reqDraft = response.requirement_draft || requirementDraft || null;
      const demAnalysis = response.demand_analysis || demandAnalysis || null;
      if (reqDraft) setRequirementDraft(reqDraft);
      if (demAnalysis) setDemandAnalysis(demAnalysis);

      // Create or populate PR Draft when ready
      let generatedPR: PRDraft | null = response.pr_draft || null;
      if (!generatedPR && response.next_agent === 'GeneratePR' && reqDraft && demAnalysis) {
        const prNumber = `PR-${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}-${Math.floor(1000 + Math.random() * 9000)}`;
        generatedPR = {
          pr_number: prNumber,
          category: reqDraft.category || 'General Procurement',
          item: reqDraft.item || 'Procured Goods',
          quantity: demAnalysis.recommended_quantity ?? reqDraft.quantity ?? 1,
          specifications: reqDraft.specifications || {},
          purpose: reqDraft.purpose || 'Internal Operations',
          required_date: reqDraft.required_date || new Date().toISOString().split('T')[0],
          business_justification: demAnalysis.justification || `Procurement for ${reqDraft.purpose}`,
          demand_analysis_summary: `Requested: ${demAnalysis.requested_quantity || reqDraft.quantity}, Stock: ${demAnalysis.available_inventory || 0}, Assets: ${demAnalysis.available_assets || 0}, Net Buy: ${demAnalysis.recommended_quantity ?? reqDraft.quantity}`,
          status: 'DRAFT',
          created_at: new Date().toISOString()
        };
      }

      if (generatedPR) {
        setPrDraft(generatedPR);
      }

      // Append Agent response message with requirement draft, demand analysis, and PR draft
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_ai`,
        role: 'assistant',
        content: response.message.content,
        timestamp: response.message.timestamp || new Date().toISOString(),
        agentName: response.next_agent === 'Demand' || response.next_agent === 'GeneratePR'
          ? 'Demand Analysis Agent'
          : 'Clarification Agent',
        requirementDraft: reqDraft,
        demandAnalysis: demAnalysis,
        prDraft: generatedPR
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

  const handleConfirmRequirement = () => {
    handleSendMessage("I confirm the extracted specifications and requirements. Please proceed to demand analysis.");
  };

  const handleEditRequirement = (updatedDraft: Partial<RequirementDraft>) => {
    const merged = { ...requirementDraft, ...updatedDraft };
    setRequirementDraft(merged as RequirementDraft);
    const summary = `Updated specifications: ${updatedDraft.quantity ? `${updatedDraft.quantity} units, ` : ''}${updatedDraft.required_date ? `Date: ${updatedDraft.required_date}, ` : ''}${updatedDraft.purpose ? `Purpose: ${updatedDraft.purpose}` : ''}`;
    handleSendMessage(summary, merged);
  };

  const handleAcceptDemand = () => {
    const recommended = demandAnalysis?.recommended_quantity ?? 0;
    handleSendMessage(`I accept the recommended purchase quantity of ${recommended} units. Please prepare the official PR draft.`);
  };

  const handleRequestOriginalDemand = () => {
    const original = demandAnalysis?.requested_quantity ?? 1;
    handleSendMessage(`I request to proceed with the original requested quantity of ${original} units due to upcoming dedicated department requirements.`);
  };

  const handleOpenPRReview = (draft?: PRDraft) => {
    if (draft) setPrDraft(draft);
    setIsReviewModalOpen(true);
  };

  const handleSavePR = (updatedPR: PRDraft) => {
    setPrDraft(updatedPR);
    setIsReviewModalOpen(false);
    const confirmationMsg: ChatMessage = {
      id: `msg_${Date.now()}_system`,
      role: 'assistant',
      content: `✅ **Purchase Requisition ${updatedPR.pr_number} Updated**\n\n• **Item:** ${updatedPR.item}\n• **Quantity:** ${updatedPR.quantity} units\n• **Required Date:** ${updatedPR.required_date}\n\nYour changes have been saved to the PR draft. Click below to submit when ready.`,
      timestamp: new Date().toISOString(),
      agentName: 'ProcureAI System',
      prDraft: updatedPR
    };
    setMessages((prev) => [...prev, confirmationMsg]);
  };

  const handleSubmitPR = (finalPR: PRDraft) => {
    setPrDraft(finalPR);
    setIsReviewModalOpen(false);
    setCurrentPhase('Completed');
    const successMsg: ChatMessage = {
      id: `msg_${Date.now()}_system`,
      role: 'assistant',
      content: `🎉 **Purchase Requisition Submitted Successfully!**\n\n• **PR Number:** \`${finalPR.pr_number}\`\n• **Item & Quantity:** ${finalPR.quantity}x ${finalPR.item}\n• **Department:** ${userContext.departmentId}\n• **Status:** \`SUBMITTED - Awaiting Manager Approval\`\n\nYour Purchase Requisition is now logged into the ERP approval queue.`,
      timestamp: new Date().toISOString(),
      agentName: 'ProcureAI System',
      prDraft: finalPR
    };
    setMessages((prev) => [...prev, successMsg]);
  };

  const handleResetThread = () => {
    const newThread = `thread_${Math.random().toString(36).substring(2, 11)}`;
    setThreadId(newThread);
    setMessages([]);
    setRequirementDraft(null);
    setDemandAnalysis(null);
    setPrDraft(null);
    setCurrentPhase('Clarification');
    setIsReviewModalOpen(false);
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
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onConfirmRequirement={handleConfirmRequirement}
          onEditRequirement={handleEditRequirement}
          onAcceptDemand={handleAcceptDemand}
          onRequestOriginalDemand={handleRequestOriginalDemand}
          onOpenPRReview={handleOpenPRReview}
          onSubmitPRDirect={(draft) => handleSubmitPR({ ...draft, status: 'SUBMITTED' })}
        />
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </main>

      {/* PR Draft Review & Edit Modal */}
      {prDraft && (
        <PRDraftReviewModal
          isOpen={isReviewModalOpen}
          onClose={() => setIsReviewModalOpen(false)}
          prDraft={prDraft}
          userContext={userContext}
          onSavePR={handleSavePR}
          onSubmitPR={handleSubmitPR}
        />
      )}
    </div>
  );
};

export default App;
