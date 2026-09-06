import React, { useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  FileCheck2,
  Loader2,
  LockKeyhole,
  PackageCheck,
  Send,
  X,
} from 'lucide-react';
import {
  ResolveWithoutPurchaseResponse,
  SubmitPRResponse,
} from '../api/requestsApi';
import {
  AttentionItem,
  PRArtifact,
  RecommendationStatus,
  RequestOutcome,
} from '../types/requests';

interface SubmissionBarProps {
  pr?: PRArtifact | null;
  attentionItems?: AttentionItem[];
  recommendationStatus: RecommendationStatus;
  requestOutcome: RequestOutcome;
  isFinalizing?: boolean;
  finalizationError?: string | null;
  submitResult?: SubmitPRResponse | null;
  resolutionResult?: ResolveWithoutPurchaseResponse | null;
  onSubmit: () => Promise<void>;
  onResolveWithoutPurchase: () => Promise<void>;
  className?: string;
}

const FINALIZATION_READY_STATUSES: RecommendationStatus[] = [
  'accepted',
  'kept_original',
  'modified',
];

export const SubmissionBar: React.FC<SubmissionBarProps> = ({
  pr,
  attentionItems = [],
  recommendationStatus,
  requestOutcome,
  isFinalizing = false,
  finalizationError = null,
  submitResult = null,
  resolutionResult = null,
  onSubmit,
  onResolveWithoutPurchase,
  className = '',
}) => {
  const [isResolutionConfirmationOpen, setIsResolutionConfirmationOpen] =
    useState(false);

  const unresolvedBlockingCount = attentionItems.filter(
    (item) => item.severity === 'blocking' && !item.resolved
  ).length;
  const recommendationIsReady = FINALIZATION_READY_STATUSES.includes(
    recommendationStatus
  );
  const isZeroPurchase = pr?.quantity === 0;
  const isSubmitted =
    pr?.status === 'submitted' ||
    requestOutcome === 'purchase_submitted' ||
    submitResult !== null;
  const isResolvedWithoutPurchase =
    pr?.status === 'not_required' ||
    requestOutcome === 'resolved_without_purchase' ||
    resolutionResult !== null;

  let disabledReason: string | null = null;
  if (unresolvedBlockingCount > 0) {
    disabledReason = `Resolve ${unresolvedBlockingCount} blocking issue${
      unresolvedBlockingCount === 1 ? '' : 's'
    } first.`;
  } else if (!recommendationIsReady) {
    disabledReason =
      recommendationStatus === 'rejected'
        ? 'This request is paused because the recommendation was rejected.'
        : 'Review the recommendation before finalizing this request.';
  }

  if (isResolvedWithoutPurchase) {
    return (
      <section
        className={`rounded-2xl border border-cyan-500/40 bg-gradient-to-r from-cyan-950/60 to-slate-900 p-5 shadow-xl shadow-cyan-950/30 animate-fade-in ${className}`}
        aria-live="polite"
      >
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-cyan-500/15 p-2.5 text-cyan-400">
            <PackageCheck className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-bold text-cyan-100">
              Request completed without a new purchase
            </p>
            <p className="mt-1 text-xs leading-relaxed text-slate-300">
              No Purchase Requisition was created or sent to ERP. The reviewed
              demand is recorded as requiring no new purchase.
            </p>
            {resolutionResult?.resolution_reason && (
              <p className="mt-2 text-[11px] italic text-cyan-200/80">
                {resolutionResult.resolution_reason}
              </p>
            )}
          </div>
        </div>
      </section>
    );
  }

  if (isSubmitted) {
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
    <>
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
                  : isZeroPurchase
                  ? 'bg-cyan-500/10 text-cyan-400'
                  : 'bg-emerald-500/10 text-emerald-400'
              }`}
            >
              {disabledReason ? (
                <LockKeyhole className="h-4 w-4" />
              ) : isZeroPurchase ? (
                <PackageCheck className="h-4 w-4" />
              ) : (
                <FileCheck2 className="h-4 w-4" />
              )}
            </div>
            <div>
              <h3
                id="submission-title"
                className="text-xs font-bold text-slate-200"
              >
                {isZeroPurchase
                  ? 'Complete Without Purchase'
                  : 'Final PR Submission'}
              </h3>
              <p
                className={`mt-0.5 text-[11px] ${
                  disabledReason
                    ? 'text-amber-300'
                    : isZeroPurchase
                    ? 'text-cyan-300'
                    : 'text-emerald-300'
                }`}
              >
                {disabledReason ||
                  (isZeroPurchase
                    ? 'Internal supply covers the reviewed demand; no ERP PR is required.'
                    : `${pr?.quantity ?? '—'} units are ready for the ERP approval queue.`)}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() =>
              isZeroPurchase
                ? setIsResolutionConfirmationOpen(true)
                : onSubmit()
            }
            disabled={Boolean(disabledReason) || isFinalizing}
            title={
              disabledReason ||
              (isZeroPurchase
                ? 'Complete this request without creating an ERP PR'
                : 'Submit this PR to the ERP approval queue')
            }
            className={`flex min-w-48 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500 ${
              isZeroPurchase
                ? 'bg-cyan-400 text-slate-950 hover:bg-cyan-300'
                : 'bg-emerald-500 text-slate-950 hover:bg-emerald-400'
            }`}
          >
            {isFinalizing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : isZeroPurchase ? (
              <PackageCheck className="h-4 w-4" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            {isFinalizing
              ? 'Finalizing...'
              : isZeroPurchase
              ? 'Complete Without Purchase'
              : 'Submit PR'}
          </button>
        </div>

        {finalizationError && (
          <div
            className="mt-3 flex items-start gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-2.5 text-[11px] text-rose-300"
            role="alert"
          >
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>{finalizationError}</span>
          </div>
        )}
      </section>

      {isResolutionConfirmationOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="resolve-without-purchase-title"
        >
          <div className="w-full max-w-md rounded-2xl border border-cyan-500/30 bg-slate-900 p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="rounded-xl bg-cyan-500/10 p-2 text-cyan-400">
                  <PackageCheck className="h-5 w-5" />
                </div>
                <div>
                  <h4
                    id="resolve-without-purchase-title"
                    className="text-sm font-bold text-white"
                  >
                    Complete without creating a PR?
                  </h4>
                  <p className="mt-2 text-xs leading-relaxed text-slate-400">
                    The reviewed final purchase quantity is 0 units. No Purchase
                    Requisition will be created or sent to ERP. The request will
                    be closed as “No Purchase Required”.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsResolutionConfirmationOpen(false)}
                disabled={isFinalizing}
                className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
                aria-label="Close confirmation dialog"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setIsResolutionConfirmationOpen(false)}
                disabled={isFinalizing}
                className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800 disabled:opacity-60"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsResolutionConfirmationOpen(false);
                  void onResolveWithoutPurchase();
                }}
                disabled={isFinalizing}
                className="flex items-center justify-center gap-2 rounded-lg bg-cyan-400 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-cyan-300 disabled:opacity-60"
              >
                {isFinalizing && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Complete Without Purchase
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
