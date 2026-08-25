import React from 'react';
import {
  FileText,
  Layers,
  Hash,
  Target,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Clock,
} from 'lucide-react';
import { PRArtifact } from '../types/requests';

interface PRArtifactCardProps {
  pr?: PRArtifact | null;
  className?: string;
}

export const PRArtifactCard: React.FC<PRArtifactCardProps> = ({
  pr,
  className = '',
}) => {
  // Empty State if no PR or item_name captured yet
  if (!pr || !pr.item_name) {
    return (
      <div
        className={`glass-panel rounded-2xl border border-dashed border-slate-800 p-6 flex flex-col items-center justify-center text-center text-slate-400 gap-3 min-h-[220px] ${className}`}
      >
        <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500">
          <FileText className="w-6 h-6 text-slate-600" />
        </div>
        <div className="flex flex-col gap-1 max-w-sm">
          <h4 className="text-xs font-semibold text-slate-300">
            No Specifications Captured Yet
          </h4>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            Start a conversation on the left panel to clarify items, quantities,
            and requirements. Structured PR drafts will appear here in real-time.
          </p>
        </div>
      </div>
    );
  }

  const isSubmitted = pr.status === 'submitted';
  const hasSpecs = pr.specifications && pr.specifications.length > 0;

  return (
    <div
      className={`glass-panel rounded-2xl border border-slate-800 p-5 flex flex-col gap-4 shadow-xl shadow-black/30 transition-all ${className}`}
    >
      {/* 1. Header: Document Title, PR Number & Status Badge */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-200">
                Purchase Requisition Artifact
              </h3>
              {pr.pr_number && (
                <span className="font-mono text-[11px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/30">
                  {pr.pr_number}
                </span>
              )}
            </div>
            <span className="text-[10px] text-slate-500">
              Department: {pr.department || 'DEPT-ENG'} · Cost Center:{' '}
              {pr.cost_center || 'CC-ENG-001'}
            </span>
          </div>
        </div>

        {/* Status Badge */}
        <span
          className={`text-[10px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full border flex items-center gap-1 ${
            isSubmitted
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
          }`}
        >
          {isSubmitted ? (
            <>
              <CheckCircle2 className="w-3 h-3" />
              Submitted
            </>
          ) : (
            <>
              <Clock className="w-3 h-3" />
              Draft
            </>
          )}
        </span>
      </div>

      {/* 2. Core Requisition Details Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
        <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800/80 flex flex-col gap-0.5">
          <span className="text-[10px] text-slate-500 flex items-center gap-1">
            <Layers className="w-3 h-3 text-indigo-400" /> Item & Category
          </span>
          <span className="font-semibold text-slate-200 truncate mt-0.5">
            {pr.item_name}
          </span>
          <span className="text-[10px] text-slate-500 truncate">
            {pr.category || 'General Supplies'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800/80 flex flex-col gap-0.5">
          <span className="text-[10px] text-slate-500 flex items-center gap-1">
            <Hash className="w-3 h-3 text-cyan-400" /> Quantity
          </span>
          <span className="font-semibold text-slate-200 text-sm mt-0.5">
            {pr.quantity ?? '—'}{' '}
            <span className="text-[10px] font-normal text-slate-400">units</span>
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800/80 flex flex-col gap-0.5">
          <span className="text-[10px] text-slate-500 flex items-center gap-1">
            <Calendar className="w-3 h-3 text-emerald-400" /> Required Date
          </span>
          <span className="font-semibold text-slate-200 mt-0.5 font-mono text-[11px]">
            {pr.required_date || '—'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800/80 flex flex-col gap-0.5">
          <span className="text-[10px] text-slate-500 flex items-center gap-1">
            <Target className="w-3 h-3 text-amber-400" /> Purpose
          </span>
          <span className="font-semibold text-slate-200 truncate mt-0.5">
            {pr.purpose || '—'}
          </span>
        </div>
      </div>

      {/* 3. Specifications List (Field-level rendering with confirmation badge) */}
      <div className="flex flex-col gap-2 pt-1 border-t border-slate-800/60">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            Technical Specifications ({pr.specifications?.length ?? 0})
          </span>
        </div>

        {hasSpecs ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {pr.specifications.map((spec, idx) => {
              const isConfirmed = Boolean(spec.is_confirmed);
              return (
                <div
                  key={`${spec.field_name}_${idx}`}
                  className={`p-2.5 rounded-xl flex items-center justify-between text-xs transition-colors ${
                    isConfirmed
                      ? 'bg-slate-900/90 border border-slate-800 text-slate-200'
                      : 'bg-slate-900/40 border border-dashed border-amber-500/40 text-slate-300'
                  }`}
                >
                  <div className="flex flex-col min-w-0 pr-2">
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider truncate">
                      {spec.field_name}
                    </span>
                    <span className="font-semibold text-slate-200 truncate text-[11px]">
                      {spec.value || 'N/A'}
                    </span>
                  </div>

                  {/* Confirmation Badge */}
                  {isConfirmed ? (
                    <span className="shrink-0 flex items-center gap-1 text-[10px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                      <CheckCircle2 className="w-3 h-3" />
                      Confirmed
                    </span>
                  ) : (
                    <span className="shrink-0 flex items-center gap-1 text-[10px] font-medium text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-full">
                      <AlertCircle className="w-3 h-3" />
                      Needs Confirmation
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <span className="text-xs text-slate-500 italic p-2 bg-slate-900/40 rounded-lg border border-slate-800">
            No specific technical parameters provided.
          </span>
        )}
      </div>
    </div>
  );
};
