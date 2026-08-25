import React from 'react';
import { RequestProgress, StageStatus } from '../types/requests';
import { CheckCircle2, Loader2, AlertCircle, RefreshCw } from 'lucide-react';

export interface RequestProgressStepperProps {
  progress?: RequestProgress;
  isLoading?: boolean;
  error?: string | null;
  className?: string;
  onRetry?: () => void;
}

interface StepConfig {
  key: keyof RequestProgress;
  title: string;
  subtitle: string;
}

const STEPS: StepConfig[] = [
  {
    key: 'clarification',
    title: 'Clarification',
    subtitle: 'Needs & Specs',
  },
  {
    key: 'demand_analysis',
    title: 'Demand Analysis',
    subtitle: 'Stock & Assets',
  },
  {
    key: 'validation',
    title: 'Validation',
    subtitle: 'Review & Policies',
  },
  {
    key: 'ready_for_submission',
    title: 'Submission',
    subtitle: 'ERP PR Queue',
  },
];

export const RequestProgressStepper: React.FC<RequestProgressStepperProps> = ({
  progress,
  isLoading = false,
  error = null,
  className = '',
  onRetry,
}) => {
  // 1. Error State: Render explicit error message instead of guessing state
  if (error) {
    return (
      <div
        className={`w-full bg-rose-950/40 border border-rose-800/60 rounded-xl p-3.5 backdrop-blur-md flex items-center justify-between gap-3 text-rose-300 text-xs ${className}`}
      >
        <div className="flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>Failed to load workflow status: {error}</span>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-1 px-2.5 py-1 bg-rose-900/60 hover:bg-rose-800 border border-rose-700 rounded text-rose-200 text-xs font-medium transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        )}
      </div>
    );
  }

  // 2. Loading State: Render skeleton placeholder while fetching
  if (isLoading && !progress) {
    return (
      <div
        className={`w-full bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 backdrop-blur-md animate-pulse ${className}`}
      >
        <div className="flex items-center justify-between">
          {STEPS.map((step, idx) => (
            <React.Fragment key={step.key}>
              <div className="flex items-center gap-3 z-10">
                <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700/60 flex items-center justify-center">
                  <div className="w-3.5 h-3.5 rounded-full bg-slate-700" />
                </div>
                <div className="hidden sm:flex flex-col gap-1.5">
                  <div className="w-20 h-3 bg-slate-800 rounded" />
                  <div className="w-14 h-2.5 bg-slate-800/60 rounded" />
                </div>
              </div>
              {idx < STEPS.length - 1 && (
                <div className="flex-1 mx-2 sm:mx-4 h-[2px] bg-slate-800" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    );
  }

  // 3. No progress data available yet
  if (!progress) {
    return null;
  }

  // 4. Normal State: Purely bound to backend progress data
  const renderStatusIcon = (status: StageStatus, stepIndex: number) => {
    switch (status) {
      case 'complete':
        return (
          <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center text-emerald-400 shadow-sm shadow-emerald-500/20">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
        );
      case 'in_progress':
        return (
          <div className="w-8 h-8 rounded-full bg-blue-500/20 border border-blue-500 flex items-center justify-center text-blue-400 shadow-sm shadow-blue-500/30 animate-pulse">
            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
          </div>
        );
      case 'blocked':
        return (
          <div className="w-8 h-8 rounded-full bg-rose-500/20 border border-rose-500/50 flex items-center justify-center text-rose-400 shadow-sm shadow-rose-500/20">
            <AlertCircle className="w-4 h-4 text-rose-400" />
          </div>
        );
      case 'pending':
      default:
        return (
          <div className="w-8 h-8 rounded-full bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-500 text-xs font-semibold">
            {stepIndex + 1}
          </div>
        );
    }
  };

  const getStatusBadge = (status: StageStatus) => {
    switch (status) {
      case 'complete':
        return (
          <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
            Done
          </span>
        );
      case 'in_progress':
        return (
          <span className="text-[10px] uppercase font-bold tracking-wider text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20">
            In Progress
          </span>
        );
      case 'blocked':
        return (
          <span className="text-[10px] uppercase font-bold tracking-wider text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
            Blocked
          </span>
        );
      case 'pending':
      default:
        return (
          <span className="text-[10px] uppercase font-medium tracking-wider text-slate-500">
            Pending
          </span>
        );
    }
  };

  return (
    <div
      className={`w-full bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 backdrop-blur-md ${className}`}
    >
      <div className="flex items-center justify-between relative">
        {STEPS.map((step, idx) => {
          const status = progress[step.key] || 'pending';
          const isLast = idx === STEPS.length - 1;
          const isLineActive = status === 'complete';

          return (
            <React.Fragment key={step.key}>
              {/* Step Node */}
              <div className="flex items-center gap-3 z-10">
                {renderStatusIcon(status, idx)}
                <div className="hidden sm:flex flex-col">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-semibold ${
                        status === 'in_progress'
                          ? 'text-blue-300'
                          : status === 'complete'
                          ? 'text-slate-200'
                          : status === 'blocked'
                          ? 'text-rose-300'
                          : 'text-slate-500'
                      }`}
                    >
                      {step.title}
                    </span>
                    {getStatusBadge(status)}
                  </div>
                  <span className="text-[11px] text-slate-400">{step.subtitle}</span>
                </div>
              </div>

              {/* Connecting Line */}
              {!isLast && (
                <div className="flex-1 mx-2 sm:mx-4 h-[2px] bg-slate-800 relative overflow-hidden rounded">
                  <div
                    className={`h-full transition-all duration-500 ${
                      isLineActive
                        ? 'w-full bg-emerald-500/60'
                        : status === 'in_progress'
                        ? 'w-1/2 bg-blue-500/60 animate-pulse'
                        : 'w-0'
                    }`}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
