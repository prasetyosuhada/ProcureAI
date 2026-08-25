import React from 'react';
import { Bot, Loader2 } from 'lucide-react';

interface TypingIndicatorProps {
  label?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  label = 'ProcureAI Agent is analyzing requirements...',
}) => {
  return (
    <div className="flex items-start gap-3 my-4 animate-fade-in">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 shrink-0">
        <Bot className="w-4 h-4" />
      </div>
      <div className="glass-card px-4 py-3 rounded-2xl rounded-tl-sm border border-slate-700/60 shadow-lg flex items-center gap-2.5">
        <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin shrink-0" />
        <span className="text-xs text-slate-300 font-medium">
          {label}
        </span>
        <div className="flex items-center gap-1 ml-1 py-1">
          <span
            className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"
            style={{ animationDelay: '0ms' }}
          />
          <span
            className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"
            style={{ animationDelay: '150ms' }}
          />
          <span
            className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </div>
    </div>
  );
};
