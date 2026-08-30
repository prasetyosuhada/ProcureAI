import React, { useEffect, useState } from 'react';
import {
  Check,
  CheckCircle2,
  Info,
  Loader2,
  Pencil,
  RotateCcw,
  Sparkles,
  X,
  XCircle,
} from 'lucide-react';
import {
  DemandBreakdown,
  RecommendationActionPayload,
  RecommendationStatus,
  RequestProgress,
} from '../types/requests';

interface RecommendationCardProps {
  demand?: DemandBreakdown | null;
  progress?: RequestProgress;
  recommendationStatus: RecommendationStatus;
  processingAction?: RecommendationActionPayload['action'] | null;
  onAction: (payload: RecommendationActionPayload) => Promise<boolean>;
  className?: string;
}

const DECISION_LABELS: Record<
  Exclude<RecommendationStatus, 'none' | 'pending_review'>,
  string
> = {
  accepted: 'AI recommendation accepted',
  kept_original: 'Original quantity retained',
  modified: 'Recommendation manually modified',
  rejected: 'Recommendation rejected — request paused',
};

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  demand,
  progress,
  recommendationStatus,
  processingAction = null,
  onAction,
  className = '',
}) => {
  const [isModifyOpen, setIsModifyOpen] = useState(false);
  const [isRejectOpen, setIsRejectOpen] = useState(false);
  const [modifiedQuantity, setModifiedQuantity] = useState('');
  const [userNotes, setUserNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    setModifiedQuantity(
      demand?.net_new_purchase !== undefined
        ? String(demand.net_new_purchase)
        : ''
    );
  }, [demand?.net_new_purchase]);

  if (
    !demand ||
    !progress ||
    progress.demand_analysis !== 'complete'
  ) {
    return null;
  }

  const hasDecision = !['none', 'pending_review'].includes(
    recommendationStatus
  );
  const isProcessing = processingAction !== null;

  const submitModification = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    const parsedQuantity = Number(modifiedQuantity);

    if (!Number.isInteger(parsedQuantity) || parsedQuantity < 0) {
      setFormError('Enter a whole number of zero or more units.');
      return;
    }
    if (!userNotes.trim()) {
      setFormError('Add a short reason for this manual quantity.');
      return;
    }

    setFormError(null);
    await onAction({
      action: 'modify',
      modification: {
        net_new_purchase: parsedQuantity,
        user_notes: userNotes.trim(),
      },
    });
  };

  const statusTone =
    recommendationStatus === 'rejected'
      ? 'border-rose-500/30 bg-rose-500/10 text-rose-300'
      : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';

  return (
    <section
      className={`glass-panel rounded-2xl border border-indigo-500/25 p-5 flex flex-col gap-4 shadow-xl shadow-black/30 animate-fade-in ${className}`}
      aria-labelledby="recommendation-title"
    >
      <div className="flex items-start justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-300">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3
              id="recommendation-title"
              className="text-sm font-bold text-slate-100"
            >
              AI Purchase Recommendation
            </h3>
            <p className="text-[11px] text-slate-400">
              Review the proposed final PR quantity before submission
            </p>
          </div>
        </div>

        {hasDecision && (
          <span
            className={`text-[10px] font-semibold px-2.5 py-1 rounded-full border ${statusTone}`}
          >
            {recommendationStatus === 'rejected' ? 'Paused' : 'Reviewed'}
          </span>
        )}
      </div>

      <div className="rounded-xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/60 to-slate-900 p-4">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-indigo-300">
          Recommended net new purchase
        </span>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="font-mono text-4xl font-black text-white">
            {demand.net_new_purchase}
          </span>
          <span className="text-xs text-slate-400">units</span>
        </div>
        <p className="mt-2 text-[11px] text-slate-400">
          From {demand.requested_qty} requested units after available stock and
          assignable assets are considered.
        </p>
      </div>

      {demand.justification && (
        <div className="flex items-start gap-2.5 rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-xs">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-cyan-400" />
          <div>
            <span className="font-semibold text-slate-300">
              Recommendation rationale
            </span>
            <p className="mt-1 whitespace-pre-line leading-relaxed text-slate-400">
              {demand.justification}
            </p>
          </div>
        </div>
      )}

      {hasDecision ? (
        <div className={`flex items-start gap-2.5 rounded-xl border p-3 ${statusTone}`}>
          {recommendationStatus === 'rejected' ? (
            <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
          ) : (
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          )}
          <div>
            <p className="text-xs font-semibold">
              {DECISION_LABELS[
                recommendationStatus as Exclude<
                  RecommendationStatus,
                  'none' | 'pending_review'
                >
              ]}
            </p>
            <p className="mt-0.5 text-[11px] opacity-80">
              {recommendationStatus === 'rejected'
                ? `The PR remains at the original ${demand.requested_qty} units and cannot be submitted.`
                : `Final PR quantity: ${demand.net_new_purchase} units.`}
            </p>
            {demand.override_reason &&
              ['modified', 'kept_original'].includes(recommendationStatus) && (
                <p className="mt-1 text-[11px] italic opacity-80">
                  {demand.override_reason}
                </p>
              )}
          </div>
        </div>
      ) : (
        <>
          {isModifyOpen && (
            <form
              onSubmit={submitModification}
              className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-3.5"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-amber-200">
                    Set a custom purchase quantity
                  </p>
                  <p className="text-[10px] text-slate-400">
                    This value becomes the final quantity on the PR.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setIsModifyOpen(false);
                    setFormError(null);
                  }}
                  className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
                  aria-label="Close modification form"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="mt-3 grid gap-3 sm:grid-cols-[130px_1fr]">
                <label className="text-[11px] font-medium text-slate-300">
                  Quantity
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={modifiedQuantity}
                    onChange={(event) =>
                      setModifiedQuantity(event.target.value)
                    }
                    disabled={isProcessing}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-xs text-white outline-none focus:border-amber-500"
                  />
                </label>
                <label className="text-[11px] font-medium text-slate-300">
                  Reason
                  <input
                    type="text"
                    value={userNotes}
                    onChange={(event) => setUserNotes(event.target.value)}
                    disabled={isProcessing}
                    placeholder="Why is this quantity needed?"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white outline-none placeholder:text-slate-600 focus:border-amber-500"
                  />
                </label>
              </div>

              {formError && (
                <p className="mt-2 text-[11px] text-rose-300">{formError}</p>
              )}

              <button
                type="submit"
                disabled={isProcessing}
                className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-amber-500 px-3 py-2 text-xs font-bold text-slate-950 transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {processingAction === 'modify' ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Pencil className="h-3.5 w-3.5" />
                )}
                Apply Custom Quantity
              </button>
            </form>
          )}

          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => onAction({ action: 'accept' })}
              disabled={isProcessing}
              className="flex min-h-12 items-center justify-center gap-2 rounded-xl bg-indigo-500 px-3 py-2 text-xs font-bold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {processingAction === 'accept' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )}
              Accept {demand.net_new_purchase} units
            </button>

            <button
              type="button"
              onClick={() => onAction({ action: 'keep_original' })}
              disabled={isProcessing}
              className="flex min-h-12 flex-col items-center justify-center rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-3 py-1.5 text-cyan-200 transition hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span className="flex items-center gap-1.5 text-xs font-bold">
                {processingAction === 'keep_original' ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <RotateCcw className="h-3.5 w-3.5" />
                )}
                Keep Original Quantity
              </span>
              <span className="text-[10px] text-cyan-300/70">
                Use {demand.requested_qty} units
              </span>
            </button>

            <button
              type="button"
              onClick={() => {
                setIsModifyOpen((current) => !current);
                setFormError(null);
              }}
              disabled={isProcessing}
              className="flex min-h-10 items-center justify-center gap-2 rounded-xl border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs font-semibold text-amber-200 transition hover:bg-amber-500/20 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Pencil className="h-3.5 w-3.5" />
              Modify
            </button>

            <button
              type="button"
              onClick={() => setIsRejectOpen(true)}
              disabled={isProcessing}
              className="flex min-h-10 items-center justify-center gap-2 rounded-xl border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-300 transition hover:bg-rose-500/20 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <XCircle className="h-3.5 w-3.5" />
              Reject & Pause
            </button>
          </div>
        </>
      )}

      {isRejectOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="reject-title"
        >
          <div className="w-full max-w-sm rounded-2xl border border-rose-500/30 bg-slate-900 p-5 shadow-2xl">
            <div className="flex items-start gap-3">
              <div className="rounded-xl bg-rose-500/10 p-2 text-rose-400">
                <XCircle className="h-5 w-5" />
              </div>
              <div>
                <h4 id="reject-title" className="text-sm font-bold text-white">
                  Reject this recommendation?
                </h4>
                <p className="mt-1 text-xs leading-relaxed text-slate-400">
                  This pauses the requisition, restores the original quantity of{' '}
                  {demand.requested_qty} units, and blocks submission.
                </p>
              </div>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setIsRejectOpen(false)}
                disabled={isProcessing}
                className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={async () => {
                  const wasSuccessful = await onAction({ action: 'reject' });
                  if (wasSuccessful) {
                    setIsRejectOpen(false);
                  }
                }}
                disabled={isProcessing}
                className="flex items-center justify-center gap-2 rounded-lg bg-rose-500 px-3 py-2 text-xs font-bold text-white hover:bg-rose-400 disabled:opacity-60"
              >
                {processingAction === 'reject' && (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                )}
                Reject Request
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
