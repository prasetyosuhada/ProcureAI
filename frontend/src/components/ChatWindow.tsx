import React, { useRef, useEffect } from 'react';
import {
  Bot,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  Loader2,
  Calendar,
  Layers,
  Hash,
  Target,
} from 'lucide-react';
import { ChatMessage } from '../types/chat';
import { PRArtifact } from '../types/requests';
import { ChatMessageBubble } from './ChatMessageBubble';
import { TypingIndicator } from './TypingIndicator';

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  isConfirming?: boolean;
  prArtifact?: PRArtifact | null;
  showConfirmPrompt?: boolean;
  onConfirmSpecifications?: () => void;
  activeAgentLabel?: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  isConfirming = false,
  prArtifact,
  showConfirmPrompt = false,
  onConfirmSpecifications,
  activeAgentLabel = 'ProcureAI is analyzing requirements...',
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, isConfirming, showConfirmPrompt]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 max-w-4xl w-full mx-auto flex flex-col justify-between">
      {messages.length === 0 ? (
        /* Empty State Hero */
        <div className="h-full flex flex-col items-center justify-center text-center py-10 px-4 animate-fade-in my-auto">
          <div className="w-14 h-14 rounded-3xl bg-gradient-to-tr from-indigo-600 via-blue-600 to-cyan-400 flex items-center justify-center text-white shadow-2xl shadow-indigo-500/30 mb-5">
            <Bot className="w-7 h-7" />
          </div>

          <h2 className="text-xl sm:text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400 mb-2.5">
            What do you need to purchase today?
          </h2>

          <p className="text-xs sm:text-sm text-slate-400 max-w-md mb-6 leading-relaxed">
            State your purchasing needs in plain text. ProcureAI will clarify
            specifications, analyze warehouse inventory & assigned assets, and prepare an
            ERP-ready Purchase Requisition (PR).
          </p>

          {/* Feature Highlight Pills */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 max-w-xl w-full text-left">
            <div className="glass-card p-3 rounded-xl border border-slate-800 flex items-start gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200">
                  1. Clarification
                </h4>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Captures specs, purpose, & timelines
                </p>
              </div>
            </div>

            <div className="glass-card p-3 rounded-xl border border-slate-800 flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200">
                  2. Demand Check
                </h4>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Deducts stock & unused assets
                </p>
              </div>
            </div>

            <div className="glass-card p-3 rounded-xl border border-slate-800 flex items-start gap-2">
              <ArrowRight className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200">
                  3. PR Validation
                </h4>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Prepares structured PR for submission
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Conversation Stream */
        <div className="space-y-1">
          {messages.map((msg) => (
            <ChatMessageBubble key={msg.id} message={msg} />
          ))}

          {/* Conditional Specification Confirmation Action Card */}
          {showConfirmPrompt && prArtifact && onConfirmSpecifications && (
            <div className="my-4 p-4 rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-indigo-500/40 shadow-xl shadow-indigo-950/30 animate-fade-in">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-bold tracking-wide uppercase text-indigo-300">
                      Specifications Captured
                    </span>
                    <span className="text-[11px] text-slate-400 block">
                      Ready to advance to Demand & Asset Analysis
                    </span>
                  </div>
                </div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/30">
                  Action Required
                </span>
              </div>

              {/* Summary Badges */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3.5 text-xs">
                <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="text-[10px] text-slate-500 flex items-center gap-1">
                    <Layers className="w-3 h-3 text-indigo-400" /> Item
                  </span>
                  <span className="font-semibold text-slate-200 truncate block mt-0.5">
                    {prArtifact.item_name || '—'}
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="text-[10px] text-slate-500 flex items-center gap-1">
                    <Hash className="w-3 h-3 text-cyan-400" /> Quantity
                  </span>
                  <span className="font-semibold text-slate-200 block mt-0.5">
                    {prArtifact.quantity ?? '—'}
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="text-[10px] text-slate-500 flex items-center gap-1">
                    <Target className="w-3 h-3 text-amber-400" /> Purpose
                  </span>
                  <span className="font-semibold text-slate-200 truncate block mt-0.5">
                    {prArtifact.purpose || '—'}
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="text-[10px] text-slate-500 flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-emerald-400" /> Date
                  </span>
                  <span className="font-semibold text-slate-200 truncate block mt-0.5">
                    {prArtifact.required_date || '—'}
                  </span>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={onConfirmSpecifications}
                disabled={isConfirming || isLoading}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-blue-600 to-teal-600 hover:from-indigo-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/25 active:scale-95 transition-all disabled:opacity-50"
              >
                {isConfirming ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Confirming & Running Demand Analysis...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Confirm Specifications & Proceed to Demand Analysis</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Processing / Inline Activity Indicator */}
          {isLoading && <TypingIndicator label={activeAgentLabel} />}

          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
};
