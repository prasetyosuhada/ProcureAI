import React, { useRef, useEffect } from 'react';
import { Bot, Sparkles, ShieldCheck, ArrowRight } from 'lucide-react';
import { ChatMessage } from '../types/chat';
import { ChatMessageBubble } from './ChatMessageBubble';
import { TypingIndicator } from './TypingIndicator';

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ messages, isLoading }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 max-w-4xl w-full mx-auto">
      {messages.length === 0 ? (
        /* Empty State Hero */
        <div className="h-full flex flex-col items-center justify-center text-center py-12 px-4 animate-fade-in">
          <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-indigo-600 via-blue-600 to-cyan-400 flex items-center justify-center text-white shadow-2xl shadow-indigo-500/30 mb-6">
            <Bot className="w-8 h-8" />
          </div>

          <h2 className="text-2xl sm:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400 mb-3">
            What do you need to purchase today?
          </h2>

          <p className="text-sm text-slate-400 max-w-md mb-8 leading-relaxed">
            State your purchasing needs in plain text. ProcureAI will clarify specifications, analyze warehouse stock & assets, and prepare an official Purchase Requisition (PR).
          </p>

          {/* Feature Highlight Pills */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-xl w-full text-left">
            <div className="glass-card p-3.5 rounded-xl border border-slate-800 flex items-start gap-2.5">
              <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200">Clarification</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">Captures specs, purpose, & timelines automatically</p>
              </div>
            </div>

            <div className="glass-card p-3.5 rounded-xl border border-slate-800 flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200">Demand Check</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">Deducts stock & unused assets from total demand</p>
              </div>
            </div>

            <div className="glass-card p-3.5 rounded-xl border border-slate-800 flex items-start gap-2.5">
              <ArrowRight className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200">PR Generation</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">Generates structured drafts for formal approval</p>
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
          {isLoading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
};
