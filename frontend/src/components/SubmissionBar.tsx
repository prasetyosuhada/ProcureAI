import React from 'react';
import {
  AlertCircle,
  CheckCircle2,
  FileCheck2,
  Loader2,
  LockKeyhole,
  Send,
} from 'lucide-react';
import { SubmitPRResponse } from '../api/requestsApi';
import {
  AttentionItem,
  PRArtifact,
  RecommendationStatus,
} from '../types/requests';

interface SubmissionBarProps {
  pr?: PRArtifact | null;
  attentionItems?: AttentionItem[];
  recommendationStatus: RecommendationStatus;
  isSubmitting?: boolean;
  submitError?: string | null;
  submitResult?: SubmitPRResponse | null;
  onSubmit: () => Promise<void>;
  className?: string;
}

const SUBMIT_READY_STATUSES: RecommendationStatus[] = [
  'accepted',
  'kept_original',
  'modified',
];

export const SubmissionBar: React.FC<SubmissionBarProps> = ({
  pr,
  attentionItems = [],
  recommendationStatus,
  isSubmitting = false,
  submitError = null,
  submitResult = null,
  onSubmit,
  className = '',
}) => {
  const unresolvedBlockingCount = attentionItems.filter(
    (item) => item.severity === 'blocking' && !item.resolved
  ).length;
  const recommendationIsReady = SUBMIT_READY_STATUSES.includes(
    recommendationStatus
  );
  const isSubmitted = pr?.status === 'submitted';

  let disabledReason: string | null = null;
  if (unresolvedBlockingCount > 0) {
    disabledReason = `Resolve ${unresolvedBlockingCount} blocking issue${
      unresolvedBlockingCount === 1 ? '' : 's'
    } first.`;
  } else if (!recommendationIsReady) {
    disabledReason =
      recommendationStatus === 'rejected'
        ? 'This request is paused because the recommendation was rejected.'
        : 'Review the recommendation before submitting.';
  }

  if (isSubmitted || submitResult) {
    const prNumber = submitResult?.pr_number || pr?.pr_number;
    return (
      <section
        className={`rounded-2xl border border-emerald-500/40 bg-gradient-to-r from-emerald-950/60 to-slate-900 p-5 shadow-xl shadow-emerald-950/30 animate-fade-in ${className}`}
        aria-live="polite"
      >
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-emerald-500/15 p-2.5 text-emerald-400">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-bold text-emerald-200">
              Purchase Requisition submitted
            </p>
            <p className="mt-1 text-xs text-slate-300">
              Your request is now in the ERP approval queue.
            </p>
            {prNumber && (
              <div className="mt-3 inline-flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5">
                <FileCheck2 className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-[10px] uppercase tracking-wider text-emerald-400">
                  PR Number
                </span>
                <span className="font-mono text-sm font-bold text-white">
                  {prNumber}
                </span>
              </div>
            )}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section
      className={`sticky bottom-4 z-10 rounded-2xl border border-slate-700/80 bg-slate-900/95 p-4 shadow-2xl shadow-black/50 backdrop-blur-xl ${className}`}
      aria-labelledby="submission-title"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-2.5">
          <div
            className={`rounded-lg p-2 ${
              disabledReason
                ? 'bg-slate-800 text-slate-500'
                : 'bg-emerald-500/10 text-emerald-400'
            }`}
          >
            {disabledReason ? (
              <LockKeyhole className="h-4 w-4" />
            ) : (
              <FileCheck2 className="h-4 w-4" />
            )}
          </div>
          <div>
            <h3 id="submission-title" className="text-xs font-bold text-slate-200">
              Final PR Submission
            </h3>
            <p
              className={`mt-0.5 text-[11px] ${
                disabledReason ? 'text-amber-300' : 'text-emerald-300'
              }`}
            >
              {disabledReason ||
                `${pr?.quantity ?? '—'} units are ready for the ERP approval queue.`}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onSubmit}
          disabled={Boolean(disabledReason) || isSubmitting}
          title={disabledReason || 'Submit this PR to the ERP approval queue'}
          className="flex min-w-40 items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-2.5 text-xs font-bold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500"
        >
          {isSubmitting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          {isSubmitting ? 'Submitting...' : 'Submit PR'}
        </button>
      </div>

      {submitError && (
        <div
          className="mt-3 flex items-start gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-2.5 text-[11px] text-rose-300"
          role="alert"
        >
          <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>{submitError}</span>
        </div>
      )}
    </section>
  );
};
