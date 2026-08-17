import React from 'react';
import { CheckCircle, ArrowDownRight, Warehouse, RefreshCw } from 'lucide-react';
import { DemandAnalysis } from '../types/chat';

interface DemandAnalysisCardProps {
  analysis: DemandAnalysis;
  onAccept?: () => void;
  onRequestOriginal?: () => void;
  disabled?: boolean;
}

export const DemandAnalysisCard: React.FC<DemandAnalysisCardProps> = ({
  analysis,
  onAccept,
  onRequestOriginal,
  disabled = false,
}) => {
  const isFulfilledInternally = (analysis.recommended_quantity || 0) === 0;

  return (
    <div className="mt-3 p-4 rounded-xl bg-slate-900/90 border border-amber-500/30 shadow-xl text-slate-100 animate-fade-in">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
            <Warehouse className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-bold tracking-wide uppercase text-amber-300">
            Demand & Inventory Evaluation
          </span>
        </div>
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">
          Optimization Report
        </span>
      </div>

      {/* Numerical Metrics Matrix */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3 text-center">
        <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-medium">Requested</span>
          <span className="text-sm font-bold text-white">{analysis.requested_quantity || 0}</span>
        </div>

        <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-medium">In Warehouse</span>
          <span className="text-sm font-bold text-cyan-400">+{analysis.available_inventory || 0}</span>
        </div>

        <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-medium">Unused Assets</span>
          <span className="text-sm font-bold text-indigo-400">+{analysis.available_assets || 0}</span>
        </div>

        <div className="bg-emerald-950/30 p-2 rounded-lg border border-emerald-500/30">
          <span className="text-[10px] text-emerald-400 block font-medium">Recommended Buy</span>
          <span className="text-sm font-bold text-emerald-300">
            {analysis.recommended_quantity || 0} units
          </span>
        </div>
      </div>

      {/* Justification Reasoning */}
      {analysis.justification && (
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 mb-3 text-xs leading-relaxed text-slate-300 flex items-start gap-2">
          {isFulfilledInternally ? (
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <ArrowDownRight className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          )}
          <div>
            <span className="font-semibold text-slate-200 block mb-0.5">Procurement Reasoning:</span>
            <span>{analysis.justification}</span>
          </div>
        </div>
      )}

      {/* Interactive Acceptance Actions */}
      <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
        {onAccept && (
          <button
            onClick={onAccept}
            disabled={disabled}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 active:scale-95 transition-all disabled:opacity-50"
          >
            <CheckCircle className="w-3.5 h-3.5" />
            <span>
              {isFulfilledInternally
                ? 'Accept Internal Fulfillment (0 New Units)'
                : `Accept Recommended Quantity (${analysis.recommended_quantity} Units)`}
            </span>
          </button>
        )}

        {onRequestOriginal && !isFulfilledInternally && (
          <button
            onClick={onRequestOriginal}
            disabled={disabled}
            className="flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-medium border border-slate-700 active:scale-95 transition-all disabled:opacity-50"
            title="Override recommendation with additional justification"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Keep {analysis.requested_quantity}</span>
          </button>
        )}
      </div>
    </div>
  );
};
