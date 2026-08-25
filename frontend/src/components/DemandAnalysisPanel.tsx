import React from 'react';
import {
  Boxes,
  Warehouse,
  RotateCcw,
  ShoppingCart,
  UserCheck,
  ShieldCheck,
  TrendingDown,
  Info,
} from 'lucide-react';
import { DemandBreakdown, RequestProgress } from '../types/requests';

interface DemandAnalysisPanelProps {
  demand?: DemandBreakdown | null;
  progress?: RequestProgress;
  className?: string;
}

export const DemandAnalysisPanel: React.FC<DemandAnalysisPanelProps> = ({
  demand,
  progress,
  className = '',
}) => {
  // Only render when demand analysis is not pending and demand data exists
  if (!progress || progress.demand_analysis === 'pending' || !demand) {
    return null;
  }

  const isOverridden = Boolean(demand.is_manually_overridden);

  // Format currency for estimated saving
  const formattedSaving =
    demand.estimated_saving !== undefined && demand.estimated_saving !== null
      ? new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          maximumFractionDigits: 0,
        }).format(demand.estimated_saving)
      : null;

  return (
    <div
      className={`glass-panel rounded-2xl border border-slate-800 p-5 flex flex-col gap-4 shadow-xl shadow-black/30 animate-fade-in ${className}`}
    >
      {/* 1. Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Boxes className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-200">
              Demand & Inventory Optimization
            </h3>
            <p className="text-[11px] text-slate-400">
              Internal warehouse stock & asset allocation check
            </p>
          </div>
        </div>

        {/* Override Badge or Automated Status */}
        {isOverridden ? (
          <span className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-amber-300 bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 rounded-full">
            <UserCheck className="w-3 h-3" />
            Manually Adjusted
          </span>
        ) : (
          <span className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 px-2.5 py-1 rounded-full">
            <ShieldCheck className="w-3 h-3" />
            AI Optimized
          </span>
        )}
      </div>

      {/* 2. Numerical Breakdown Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
        <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800/80 flex flex-col gap-0.5">
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <ShoppingCart className="w-3 h-3 text-slate-400" /> Requested
          </span>
          <span className="text-base font-bold text-slate-200 mt-0.5">
            {demand.requested_qty}
          </span>
          <span className="text-[10px] text-slate-500">Total requested</span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800/80 flex flex-col gap-0.5">
          <span className="text-[10px] text-emerald-400 flex items-center gap-1">
            <Warehouse className="w-3 h-3 text-emerald-400" /> Stock Deducted
          </span>
          <span className="text-base font-bold text-emerald-400 mt-0.5">
            {demand.existing_inventory}
          </span>
          <span className="text-[10px] text-slate-500">Warehouse stock</span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800/80 flex flex-col gap-0.5">
          <span className="text-[10px] text-cyan-400 flex items-center gap-1">
            <RotateCcw className="w-3 h-3 text-cyan-400" /> Assignable Assets
          </span>
          <span className="text-base font-bold text-cyan-400 mt-0.5">
            {demand.assignable_assets}
          </span>
          <span className="text-[10px] text-slate-500">Returning / idle</span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800/80 flex flex-col gap-0.5">
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <Boxes className="w-3 h-3 text-slate-400" /> Reserved
          </span>
          <span className="text-base font-bold text-slate-400 mt-0.5">
            {demand.reserved_qty}
          </span>
          <span className="text-[10px] text-slate-500">Pipeline holds</span>
        </div>
      </div>

      {/* 3. Recommendation Result Box */}
      <div className="p-3.5 rounded-xl bg-gradient-to-r from-indigo-950/40 via-slate-900 to-teal-950/30 border border-indigo-500/30 flex items-center justify-between gap-4">
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-indigo-300">
            Recommended Net New Purchase
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono">
              {demand.net_new_purchase}
            </span>
            <span className="text-xs text-slate-400">units to procure</span>
          </div>
        </div>

        {formattedSaving && (
          <div className="flex flex-col items-end gap-0.5">
            <span className="text-[10px] text-emerald-400 font-medium flex items-center gap-1">
              <TrendingDown className="w-3 h-3" /> Cost Avoidance
            </span>
            <span className="text-sm font-bold text-emerald-300 font-mono">
              {formattedSaving}
            </span>
          </div>
        )}
      </div>

      {/* 4. Manual Adjustment Callout (if overridden) */}
      {isOverridden && (
        <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 flex items-start gap-2.5 text-xs text-amber-200">
          <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="flex flex-col gap-0.5">
            <span className="font-semibold text-amber-300">
              Requester Manual Override Active
            </span>
            <p className="text-[11px] text-amber-200/90 leading-relaxed">
              {demand.override_reason ||
                'Quantity adjusted manually by the requester for operational buffer.'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
