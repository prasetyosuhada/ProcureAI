import React from 'react';
import { RequestProgress, StageStatus } from '../types/requests';
import { CheckCircle2, Loader2, AlertCircle } from 'lucide-react';

interface RequestProgressStepperProps {
  progress?: RequestProgress;
  className?: string;
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
  className = '',
}) => {
  // Default fallback if progress is undefined
  const defaultProgress: RequestProgress = {
    clarification: 'in_progress',
    demand_analysis: 'pending',
    validation: 'pending',
    ready_for_submission: 'pending',
  };

  const currentProgress = progress || defaultProgress;

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
          const status = currentProgress[step.key] || 'pending';
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
