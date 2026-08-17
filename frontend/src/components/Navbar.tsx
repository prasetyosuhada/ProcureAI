import React from 'react';
import { Bot, Sparkles, Building2, User, CheckCircle2, Clock } from 'lucide-react';
import { UserContext } from '../types/chat';

interface NavbarProps {
  userContext: UserContext;
  currentPhase: 'Clarification' | 'Demand' | 'GeneratePR' | 'Completed';
  threadId: string;
}

export const Navbar: React.FC<NavbarProps> = ({ userContext, currentPhase, threadId }) => {
  const getPhaseBadge = () => {
    switch (currentPhase) {
      case 'Clarification':
        return (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-medium animate-pulse">
            <Clock className="w-3.5 h-3.5" />
            <span>Phase 1: Clarification</span>
          </div>
        );
      case 'Demand':
        return (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium animate-pulse">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Phase 2: Demand Analysis</span>
          </div>
        );
      case 'GeneratePR':
      case 'Completed':
        return (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Phase 3: PR Draft</span>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <header className="sticky top-0 z-30 w-full glass-panel border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
                ProcureAI
              </span>
              <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                Agentic MVP
              </span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-2">
              <span>Intelligent PR Generation & Demand Analysis</span>
              <span className="text-slate-600">•</span>
              <span className="font-mono text-[11px] text-slate-500">{threadId}</span>
            </p>
          </div>
        </div>

        {/* Workflow Phase Indicator */}
        <div className="hidden md:flex items-center gap-3">
          {getPhaseBadge()}
        </div>

        {/* User Context & Meta Badges */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex flex-col items-end text-right text-xs">
            <div className="flex items-center gap-1 text-slate-200 font-medium">
              <User className="w-3.5 h-3.5 text-indigo-400" />
              <span>{userContext.userName}</span>
            </div>
            <div className="flex items-center gap-1 text-slate-400 text-[11px]">
              <Building2 className="w-3 h-3 text-slate-500" />
              <span>{userContext.departmentId} ({userContext.costCenter})</span>
            </div>
          </div>
          <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-sm font-semibold text-indigo-400">
            {userContext.userName.charAt(0)}
          </div>
        </div>
      </div>
    </header>
  );
};
