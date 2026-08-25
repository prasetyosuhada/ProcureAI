import React, { useState } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { AgentAction } from '../types/requests';

interface AgentActivityStripProps {
  activities?: AgentAction[];
  className?: string;
}

export const AgentActivityStrip: React.FC<AgentActivityStripProps> = ({
  activities = [],
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  // If no activities recorded yet, do not render
  if (!activities || activities.length === 0) {
    return null;
  }

  // Display items in reverse chronological order (latest on top)
  const sortedActivities = [...activities].reverse();
  const displayedActivities = isExpanded
    ? sortedActivities
    : sortedActivities.slice(0, 3);

  const hasMore = activities.length > 3;

  return (
    <div
      className={`glass-panel rounded-2xl border border-slate-800/80 p-4 flex flex-col gap-3 shadow-lg shadow-black/20 animate-fade-in ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-bold text-slate-300">
            Agent Actions & Telemetry
          </span>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded-full border border-slate-800">
            {activities.length} total
          </span>
        </div>

        {hasMore && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 transition-colors"
          >
            <span>{isExpanded ? 'Show less' : `Show all (${activities.length})`}</span>
            {isExpanded ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </button>
        )}
      </div>

      {/* Activity Items List */}
      <div className="flex flex-col gap-2">
        {displayedActivities.map((act, idx) => {
          const isDone = act.status === 'done';
          const isFailed = act.status === 'failed';
          const isRunning = act.status === 'running';

          return (
            <div
              key={idx}
              className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/70 flex items-start gap-2.5 text-xs transition-all hover:bg-slate-900"
            >
              {/* Status Icon */}
              <div className="mt-0.5 shrink-0">
                {isDone && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                )}
                {isFailed && (
                  <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                )}
                {isRunning && (
                  <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
                )}
              </div>

              {/* Action Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-slate-200 truncate">
                    {act.label}
                  </span>
                  <span
                    className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded ${
                      isDone
                        ? 'text-emerald-400 bg-emerald-500/10'
                        : isFailed
                        ? 'text-rose-400 bg-rose-500/10'
                        : 'text-indigo-400 bg-indigo-500/10'
                    }`}
                  >
                    {act.status}
                  </span>
                </div>

                {act.result_summary && (
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-normal">
                    {act.result_summary}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
