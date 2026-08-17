import React from 'react';
import { FileText, Eye, CheckCircle2, Calendar, Hash } from 'lucide-react';
import { PRDraft } from '../types/chat';

interface PRDraftCardProps {
  prDraft: PRDraft;
  onOpenReview: () => void;
  onSubmitDirect?: () => void;
  disabled?: boolean;
}

export const PRDraftCard: React.FC<PRDraftCardProps> = ({
  prDraft,
  onOpenReview,
  onSubmitDirect,
  disabled = false,
}) => {
  const isSubmitted = prDraft.status === 'SUBMITTED';

  return (
    <div className="mt-3 p-4 rounded-xl bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 border border-emerald-500/40 shadow-xl text-slate-100 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center shadow-sm">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold tracking-wide uppercase text-emerald-300 block">
              Purchase Requisition Ready
            </span>
            <span className="font-mono text-[11px] text-slate-400">{prDraft.pr_number}</span>
          </div>
        </div>
        <span
          className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full border ${
            isSubmitted
              ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
          }`}
        >
          {isSubmitted ? 'Submitted' : 'Draft / Ready for Review'}
        </span>
      </div>

      {/* Snapshot Summary Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 mb-3 text-xs">
        <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-medium">Requisitioned Item</span>
          <span className="font-semibold text-white truncate block">{prDraft.item}</span>
          <span className="text-[11px] text-slate-400 truncate block">{prDraft.category}</span>
        </div>

        <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-medium">Approved Quantity</span>
          <div className="flex items-center gap-1 mt-0.5">
            <Hash className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-bold text-sm text-cyan-300">{prDraft.quantity} units</span>
          </div>
        </div>

        <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800 col-span-2 sm:col-span-1">
          <span className="text-[10px] text-slate-400 block font-medium">Required By</span>
          <div className="flex items-center gap-1 mt-0.5">
            <Calendar className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-medium text-white">{prDraft.required_date || 'Flexible'}</span>
          </div>
        </div>
      </div>

      {/* Demand Justification Preview */}
      {prDraft.demand_analysis_summary && (
        <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800 mb-3 text-xs text-slate-300">
          <span className="text-[10px] text-slate-400 font-medium block mb-0.5">
            Optimization & Inventory Summary:
          </span>
          <p className="line-clamp-2 leading-relaxed text-slate-300">{prDraft.demand_analysis_summary}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
        <button
          onClick={onOpenReview}
          disabled={disabled}
          className="flex-1 flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 active:scale-95 transition-all disabled:opacity-50"
        >
          <Eye className="w-3.5 h-3.5" />
          <span>Review & Edit Full PR Form</span>
        </button>

        {onSubmitDirect && !isSubmitted && (
          <button
            onClick={onSubmitDirect}
            disabled={disabled}
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 active:scale-95 transition-all disabled:opacity-50"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Submit PR</span>
          </button>
        )}
      </div>
    </div>
  );
};
