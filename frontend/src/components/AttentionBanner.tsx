import React from 'react';
import {
  AlertTriangle,
  BellRing,
  CheckCircle2,
  Loader2,
  ShieldAlert,
} from 'lucide-react';
import { AttentionItem } from '../types/requests';

interface AttentionBannerProps {
  items?: AttentionItem[];
  resolvingItemId?: string | null;
  onResolve: (itemId: string) => Promise<void>;
  className?: string;
}

export const AttentionBanner: React.FC<AttentionBannerProps> = ({
  items = [],
  resolvingItemId = null,
  onResolve,
  className = '',
}) => {
  const unresolvedItems = items
    .filter((item) => !item.resolved)
    .sort((left, right) =>
      left.severity === right.severity
        ? 0
        : left.severity === 'blocking'
        ? -1
        : 1
    );

  if (unresolvedItems.length === 0) {
    return null;
  }

  const blockingCount = unresolvedItems.filter(
    (item) => item.severity === 'blocking'
  ).length;

  return (
    <section
      className={`rounded-2xl border border-amber-500/25 bg-amber-950/20 p-4 animate-fade-in ${className}`}
      aria-labelledby="attention-title"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <BellRing className="h-4 w-4 text-amber-400" />
          <div>
            <h3 id="attention-title" className="text-xs font-bold text-amber-100">
              Items requiring attention
            </h3>
            <p className="text-[10px] text-slate-400">
              {blockingCount > 0
                ? `${blockingCount} blocking issue${blockingCount === 1 ? '' : 's'} must be resolved before submission.`
                : 'Review these warnings before submitting your requisition.'}
            </p>
          </div>
        </div>
        <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold text-amber-300">
          {unresolvedItems.length} open
        </span>
      </div>

      <div className="grid gap-2 lg:grid-cols-2">
        {unresolvedItems.map((item) => {
          const isBlocking = item.severity === 'blocking';
          const isResolving = resolvingItemId === item.id;

          return (
            <article
              key={item.id}
              className={`flex items-start gap-3 rounded-xl border p-3 ${
                isBlocking
                  ? 'border-rose-500/40 bg-rose-950/40'
                  : 'border-amber-500/30 bg-slate-900/60'
              }`}
            >
              {isBlocking ? (
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-rose-400" />
              ) : (
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
              )}
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span
                    className={`text-[9px] font-bold uppercase tracking-wider ${
                      isBlocking ? 'text-rose-300' : 'text-amber-300'
                    }`}
                  >
                    {item.severity}
                  </span>
                  <span className="text-[9px] uppercase text-slate-500">
                    {item.category}
                  </span>
                </div>
                <p className="mt-1 text-[11px] leading-relaxed text-slate-300">
                  {item.message}
                </p>
                <button
                  type="button"
                  onClick={() => onResolve(item.id)}
                  disabled={resolvingItemId !== null}
                  className={`mt-2 flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[10px] font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                    isBlocking
                      ? 'border-rose-500/40 text-rose-200 hover:bg-rose-500/10'
                      : 'border-amber-500/40 text-amber-200 hover:bg-amber-500/10'
                  }`}
                >
                  {isResolving ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-3 w-3" />
                  )}
                  Resolve
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
};
