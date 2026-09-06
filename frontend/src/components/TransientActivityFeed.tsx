import React from 'react';
import { Bot, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { TransientActivity } from '../types/requests';

interface TransientActivityFeedProps {
  activities: TransientActivity[];
  isFading?: boolean;
}

export const TransientActivityFeed: React.FC<
  TransientActivityFeedProps
> = ({ activities, isFading = false }) => {
  if (activities.length === 0) return null;

  return (
    <div
      data-testid="transient-activity-feed"
      aria-live="polite"
      className={`my-4 flex items-start gap-3 transition-opacity duration-500 ${
        isFading ? 'opacity-0' : 'opacity-100'
      }`}
    >
      <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 shrink-0">
        <Bot className="w-4 h-4" />
      </div>
      <div className="min-w-0 flex-1 rounded-2xl rounded-tl-sm border border-indigo-500/25 bg-slate-900/80 px-4 py-3 shadow-lg">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-indigo-300">
          ProcureAI is working
        </p>
        <div className="space-y-2">
          {activities.map((activity) => (
            <div
              key={activity.id}
              data-activity-id={activity.id}
              className="flex items-start gap-2 text-xs"
            >
              {activity.status === 'running' ? (
                <Loader2 className="mt-0.5 h-3.5 w-3.5 shrink-0 animate-spin text-indigo-400" />
              ) : activity.status === 'failed' ? (
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-400" />
              ) : (
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />
              )}
              <div className="min-w-0">
                <p
                  className={`font-medium ${
                    activity.status === 'failed'
                      ? 'text-rose-300'
                      : 'text-slate-200'
                  }`}
                >
                  {activity.label}
                </p>
                {activity.result_summary && (
                  <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400">
                    {activity.result_summary}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
