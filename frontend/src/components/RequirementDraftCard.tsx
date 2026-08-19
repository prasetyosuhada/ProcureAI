import React, { useState } from 'react';
import { CheckCircle2, Edit3, Layers, Calendar, Hash, Target, Cpu, ArrowRight, ShieldCheck, Check } from 'lucide-react';
import { RequirementDraft } from '../types/chat';

interface RequirementDraftCardProps {
  draft: RequirementDraft;
  onConfirm?: () => void;
  onEdit?: (updatedDraft: Partial<RequirementDraft>) => void;
  disabled?: boolean;
  isConfirmed?: boolean;
}

export const RequirementDraftCard: React.FC<RequirementDraftCardProps> = ({
  draft,
  onConfirm,
  onEdit,
  disabled = false,
  isConfirmed = false,
}) => {
  // Requirement summary should ONLY appear when all mandatory fields are complete
  if (!draft || !draft.is_complete) {
    return null;
  }

  const [isEditing, setIsEditing] = useState(false);
  const [editQuantity, setEditQuantity] = useState(draft.quantity || 1);
  const [editDate, setEditDate] = useState(draft.required_date || '');
  const [editPurpose, setEditPurpose] = useState(draft.purpose || '');

  const handleSaveEdit = () => {
    if (onEdit) {
      onEdit({
        quantity: Number(editQuantity),
        required_date: editDate,
        purpose: editPurpose,
      });
    }
    setIsEditing(false);
  };

  const specsEntries = Object.entries(draft.specifications || {});

  return (
    <div className="w-full rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-emerald-500/30 shadow-xl shadow-emerald-950/20 text-slate-100 p-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold tracking-wide uppercase text-emerald-400">
              Requirement Summary
            </span>
            <span className="text-[10px] text-slate-400 block">
              Specifications verified · Ready for demand analysis
            </span>
          </div>
        </div>

        <span
          className={`text-[10px] font-semibold px-2.5 py-1 rounded-full border flex items-center gap-1 ${
            isConfirmed
              ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
          }`}
        >
          {isConfirmed ? (
            <>
              <Check className="w-3 h-3" />
              Confirmed
            </>
          ) : (
            <>
              <CheckCircle2 className="w-3 h-3" />
              Pending Confirmation
            </>
          )}
        </span>
      </div>

      {!isEditing ? (
        <>
          {/* Spec Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
            <div className="flex items-start gap-2 bg-slate-950/80 p-2.5 rounded-xl border border-slate-800/80">
              <Layers className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <div className="min-w-0">
                <span className="text-[10px] text-slate-400 block font-medium">Item & Category</span>
                <span className="font-semibold text-white truncate block">{draft.item || 'Not specified'}</span>
                {draft.category && (
                  <span className="text-[11px] text-slate-400 block truncate">{draft.category}</span>
                )}
              </div>
            </div>

            <div className="flex items-start gap-2 bg-slate-950/80 p-2.5 rounded-xl border border-slate-800/80">
              <Hash className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <div>
                <span className="text-[10px] text-slate-400 block font-medium">Quantity</span>
                <span className="font-semibold text-white">
                  {draft.quantity ? `${draft.quantity} units` : '1 unit'}
                </span>
              </div>
            </div>

            <div className="flex items-start gap-2 bg-slate-950/80 p-2.5 rounded-xl border border-slate-800/80">
              <Target className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
              <div className="min-w-0">
                <span className="text-[10px] text-slate-400 block font-medium">Purpose</span>
                <span className="font-semibold text-white truncate block">{draft.purpose || 'Internal Team'}</span>
              </div>
            </div>

            <div className="flex items-start gap-2 bg-slate-950/80 p-2.5 rounded-xl border border-slate-800/80">
              <Calendar className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="text-[10px] text-slate-400 block font-medium">Required Date</span>
                <span className="font-semibold text-white">{draft.required_date || 'Flexible'}</span>
              </div>
            </div>
          </div>

          {/* Technical Specifications */}
          {specsEntries.length > 0 && (
            <div className="mt-2.5 bg-slate-950/80 p-2.5 rounded-xl border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-medium mb-1.5">
                <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                <span>Technical Specifications</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {specsEntries.map(([key, value]) => (
                  <span
                    key={key}
                    className="px-2 py-0.5 rounded-md bg-indigo-950/60 text-indigo-300 text-[11px] font-mono border border-indigo-800/40"
                  >
                    {key}: {String(value)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {!isConfirmed && (
            <div className="flex flex-col sm:flex-row items-center gap-2 mt-3 pt-3 border-t border-slate-800/80">
              {onConfirm && (
                <button
                  onClick={onConfirm}
                  disabled={disabled}
                  className="w-full sm:flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-emerald-700/20 active:scale-95 transition-all disabled:opacity-50"
                >
                  <ArrowRight className="w-4 h-4" />
                  <span>Confirm & Proceed to Demand Analysis</span>
                </button>
              )}

              <button
                onClick={() => setIsEditing(true)}
                disabled={disabled}
                className="w-full sm:w-auto flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 active:scale-95 transition-all disabled:opacity-50"
              >
                <Edit3 className="w-3.5 h-3.5 text-slate-400" />
                <span>Edit</span>
              </button>
            </div>
          )}
        </>
      ) : (
        /* Edit Form */
        <div className="space-y-2.5 text-xs">
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Quantity</label>
            <input
              type="number"
              min="1"
              value={editQuantity}
              onChange={(e) => setEditQuantity(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500 text-xs"
            />
          </div>
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Target Date</label>
            <input
              type="text"
              value={editDate}
              onChange={(e) => setEditDate(e.target.value)}
              placeholder="e.g. 2026-09-01"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500 text-xs"
            />
          </div>
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Purpose</label>
            <input
              type="text"
              value={editPurpose}
              onChange={(e) => setEditPurpose(e.target.value)}
              placeholder="e.g. Backend Development Team"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500 text-xs"
            />
          </div>

          <div className="flex items-center gap-2 pt-2">
            <button
              onClick={handleSaveEdit}
              className="flex-1 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all"
            >
              Save Changes
            </button>
            <button
              onClick={() => setIsEditing(false)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs transition-all"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
