import React, { useState } from 'react';
import {
  X,
  FileText,
  Building2,
  Calendar,
  Layers,
  Hash,
  Target,
  Cpu,
  Copy,
  Check,
  Send,
  Sparkles,
} from 'lucide-react';
import { PRDraft, UserContext } from '../types/chat';

interface PRDraftReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  prDraft: PRDraft;
  userContext: UserContext;
  onSavePR: (updatedPR: PRDraft) => void;
  onSubmitPR: (finalPR: PRDraft) => void;
}

export const PRDraftReviewModal: React.FC<PRDraftReviewModalProps> = ({
  isOpen,
  onClose,
  prDraft,
  userContext,
  onSavePR,
  onSubmitPR,
}) => {
  const [formData, setFormData] = useState<PRDraft>({ ...prDraft });
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'form' | 'json'>('form');

  if (!isOpen) return null;

  const handleInputChange = (field: keyof PRDraft, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSpecChange = (key: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      specifications: {
        ...(prev.specifications || {}),
        [key]: value,
      },
    }));
  };

  const handleSave = () => {
    onSavePR(formData);
  };

  const handleSubmit = () => {
    const finalPayload = { ...formData, status: 'SUBMITTED' };
    onSubmitPR(finalPayload);
  };

  const handleCopySummary = () => {
    const summaryText = `Purchase Requisition: ${formData.pr_number}\nItem: ${formData.item} (${formData.category})\nQuantity: ${formData.quantity}\nRequired Date: ${formData.required_date}\nPurpose: ${formData.purpose}\nJustification: ${formData.business_justification}\nDemand Deduction Summary: ${formData.demand_analysis_summary}`;
    navigator.clipboard.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl glass-panel border border-slate-700/80 shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">Purchase Requisition Review</h3>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
                  {formData.pr_number}
                </span>
              </div>
              <p className="text-xs text-slate-400">Review, edit, and confirm PR details before official submission</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab(activeTab === 'form' ? 'json' : 'form')}
              className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 hover:text-white text-xs font-mono border border-slate-700 transition-all"
            >
              {activeTab === 'form' ? '{ JSON }' : 'Form View'}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Metadata Ribbon */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs">
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-400" />
              <div>
                <span className="text-[10px] text-slate-500 block">Department & Cost Center</span>
                <span className="font-medium text-slate-200">
                  {userContext.departmentId} ({userContext.costCenter})
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-amber-400" />
              <div>
                <span className="text-[10px] text-slate-500 block">Requestor</span>
                <span className="font-medium text-slate-200">{userContext.userName}</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <div>
                <span className="text-[10px] text-slate-500 block">Status</span>
                <span className="font-semibold text-emerald-400">
                  {formData.status || 'DRAFT (Ready to Submit)'}
                </span>
              </div>
            </div>
          </div>

          {activeTab === 'form' ? (
            /* Structured Form View */
            <div className="space-y-4 text-xs">
              {/* Basic Details Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1 mb-1">
                    <Layers className="w-3.5 h-3.5 text-indigo-400" />
                    Item Name
                  </label>
                  <input
                    type="text"
                    value={formData.item}
                    onChange={(e) => handleInputChange('item', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl p-2.5 text-white focus:outline-none focus:border-indigo-500 text-xs"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1 mb-1">
                    <Layers className="w-3.5 h-3.5 text-indigo-400" />
                    Product Category
                  </label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={(e) => handleInputChange('category', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl p-2.5 text-white focus:outline-none focus:border-indigo-500 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1 mb-1">
                    <Hash className="w-3.5 h-3.5 text-cyan-400" />
                    Approved Purchase Quantity
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.quantity}
                    onChange={(e) => handleInputChange('quantity', Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl p-2.5 text-white focus:outline-none focus:border-indigo-500 text-xs font-semibold"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1 mb-1">
                    <Calendar className="w-3.5 h-3.5 text-amber-400" />
                    Required Delivery Date
                  </label>
                  <input
                    type="text"
                    value={formData.required_date}
                    onChange={(e) => handleInputChange('required_date', e.target.value)}
                    placeholder="YYYY-MM-DD"
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl p-2.5 text-white focus:outline-none focus:border-indigo-500 text-xs"
                  />
                </div>
              </div>

              {/* Purpose */}
              <div>
                <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1 mb-1">
                  <Target className="w-3.5 h-3.5 text-violet-400" />
                  Business Purpose & User Allocation
                </label>
                <input
                  type="text"
                  value={formData.purpose}
                  onChange={(e) => handleInputChange('purpose', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl p-2.5 text-white focus:outline-none focus:border-indigo-500 text-xs"
                />
              </div>

              {/* Technical Specifications */}
              <div>
                <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1 mb-1">
                  <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                  Technical Specifications
                </label>
                <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                  {Object.entries(formData.specifications || {}).map(([key, val]) => (
                    <div key={key} className="flex items-center gap-2">
                      <span className="w-28 text-slate-400 font-mono capitalize">{key}:</span>
                      <input
                        type="text"
                        value={String(val)}
                        onChange={(e) => handleSpecChange(key, e.target.value)}
                        className="flex-1 bg-slate-900 border border-slate-700/80 rounded-lg px-2.5 py-1 text-white text-xs focus:outline-none focus:border-indigo-500 font-mono"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Business Justification */}
              <div>
                <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                  Business Justification (AI Generated & Verified)
                </label>
                <textarea
                  rows={2}
                  value={formData.business_justification}
                  onChange={(e) => handleInputChange('business_justification', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl p-2.5 text-white focus:outline-none focus:border-indigo-500 text-xs leading-relaxed"
                />
              </div>

              {/* Demand Analysis Summary */}
              <div>
                <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                  Demand & Warehouse Inventory Summary
                </label>
                <textarea
                  rows={2}
                  value={formData.demand_analysis_summary}
                  onChange={(e) => handleInputChange('demand_analysis_summary', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl p-2.5 text-white focus:outline-none focus:border-indigo-500 text-xs leading-relaxed"
                />
              </div>
            </div>
          ) : (
            /* JSON View */
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-x-auto">
              <pre className="text-emerald-400 font-mono text-xs leading-relaxed">
                {JSON.stringify(formData, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/60">
          <button
            onClick={handleCopySummary}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium border border-slate-700 transition-all active:scale-95"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied to Clipboard' : 'Copy Summary'}</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700 transition-all active:scale-95"
            >
              Save Draft
            </button>

            <button
              onClick={handleSubmit}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white text-xs font-semibold shadow-lg shadow-emerald-600/30 transition-all active:scale-95"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Submit Requisition</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
