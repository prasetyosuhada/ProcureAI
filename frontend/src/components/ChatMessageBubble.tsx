import React from 'react';
import { User, Bot, Sparkles, CheckCheck } from 'lucide-react';
import { ChatMessage, RequirementDraft, PRDraft } from '../types/chat';
import { RequirementDraftCard } from './RequirementDraftCard';
import { DemandAnalysisCard } from './DemandAnalysisCard';
import { PRDraftCard } from './PRDraftCard';

interface ChatMessageBubbleProps {
  message: ChatMessage;
  onConfirmRequirement?: () => void;
  onEditRequirement?: (updatedDraft: Partial<RequirementDraft>) => void;
  onAcceptDemand?: () => void;
  onRequestOriginalDemand?: () => void;
  onOpenPRReview?: (draft: PRDraft) => void;
  onSubmitPRDirect?: (draft: PRDraft) => void;
}

export const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({
  message,
  onConfirmRequirement,
  onEditRequirement,
  onAcceptDemand,
  onRequestOriginalDemand,
  onOpenPRReview,
  onSubmitPRDirect,
}) => {
  const isUser = message.role === 'user';

  // Simple clean formatting for markdown bold and bullet points
  const formatContent = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) {
        return <div key={idx} className="h-2" />;
      }

      // Check if bullet point
      const isBullet = trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('*');
      const cleanLine = isBullet ? trimmed.replace(/^[•\-\*]\s*/, '') : line;

      // Simple regex bold replacement
      const parts = cleanLine.split(/(\*\*.*?\*\*)/g);
      const formattedParts = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={pIdx} className="font-semibold text-white">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return part;
      });

      if (isBullet) {
        return (
          <div key={idx} className="flex items-start gap-2 my-1 text-slate-200">
            <span className="text-indigo-400 font-bold">•</span>
            <span>{formattedParts}</span>
          </div>
        );
      }

      return (
        <p key={idx} className="my-1 leading-relaxed text-slate-200">
          {formattedParts}
        </p>
      );
    });
  };

  return (
    <div
      className={`flex items-start gap-3 my-4 ${
        isUser ? 'flex-row-reverse' : 'flex-row'
      }`}
    >
      {/* Avatar Icon */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
          isUser
            ? 'bg-gradient-to-tr from-slate-700 to-slate-600 text-slate-200 border border-slate-600'
            : 'bg-gradient-to-tr from-indigo-600 to-blue-600 text-white shadow-indigo-500/20'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message Bubble Container */}
      <div
        className={`max-w-[90%] sm:max-w-[80%] rounded-2xl px-4 py-3 shadow-lg ${
          isUser
            ? 'bg-indigo-600 text-white rounded-tr-sm'
            : 'glass-card border border-slate-700/60 rounded-tl-sm'
        }`}
      >
        {/* Header (Agent label / User label) */}
        <div className="flex items-center justify-between gap-4 mb-1.5 pb-1 border-b border-white/5">
          <span
            className={`text-xs font-semibold ${
              isUser ? 'text-indigo-200' : 'text-indigo-400 flex items-center gap-1'
            }`}
          >
            {!isUser && <Sparkles className="w-3 h-3" />}
            {isUser ? 'You' : (message.agentName || 'ProcureAI Agent')}
          </span>
          <span className="text-[10px] text-slate-400 font-mono">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {/* Message Text Content */}
        <div className="text-sm font-normal">
          {formatContent(message.content)}
        </div>

        {/* Interactive Widget 1: Requirement Draft Card */}
        {message.requirementDraft && (
          <RequirementDraftCard
            draft={message.requirementDraft}
            onConfirm={onConfirmRequirement}
            onEdit={onEditRequirement}
          />
        )}

        {/* Interactive Widget 2: Demand Analysis Optimization Card */}
        {message.demandAnalysis && (
          <DemandAnalysisCard
            analysis={message.demandAnalysis}
            onAccept={onAcceptDemand}
            onRequestOriginal={onRequestOriginalDemand}
          />
        )}

        {/* Interactive Widget 3: PR Draft Ready Card */}
        {message.prDraft && (
          <PRDraftCard
            prDraft={message.prDraft}
            onOpenReview={() => onOpenPRReview && onOpenPRReview(message.prDraft!)}
            onSubmitDirect={() => onSubmitPRDirect && onSubmitPRDirect(message.prDraft!)}
          />
        )}

        {/* Read Receipt Icon for User */}
        {isUser && (
          <div className="flex justify-end mt-1">
            <CheckCheck className="w-3.5 h-3.5 text-indigo-300 opacity-80" />
          </div>
        )}
      </div>
    </div>
  );
};
