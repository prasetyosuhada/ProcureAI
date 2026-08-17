import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Laptop, Armchair, Monitor } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading, disabled }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const samplePrompts = [
    { label: '10 Laptops for Backend Team', icon: Laptop, text: 'I need 10 laptops for backend development before Sept 1 with 32GB RAM and 1TB SSD' },
    { label: '5 Ergonomic Chairs', icon: Armchair, text: 'We need 5 ergonomic chairs for operations team delivered next month' },
    { label: '2 4K Monitors', icon: Monitor, text: 'Need 2 4K monitors for UI/UX designers before Sept 15' },
  ];

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading || disabled) return;
    onSendMessage(trimmed);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handlePromptClick = (text: string) => {
    if (isLoading || disabled) return;
    onSendMessage(text);
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4">
      {/* Quick Starter Suggestions */}
      <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-1 no-scrollbar">
        <span className="text-[11px] text-slate-500 font-medium flex items-center gap-1 shrink-0">
          <Sparkles className="w-3 h-3 text-indigo-400" />
          Quick start:
        </span>
        {samplePrompts.map((item, idx) => {
          const Icon = item.icon;
          return (
            <button
              key={idx}
              onClick={() => handlePromptClick(item.text)}
              disabled={isLoading || disabled}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-slate-900/80 hover:bg-indigo-950/60 border border-slate-800 hover:border-indigo-500/40 text-slate-300 hover:text-indigo-300 transition-all shrink-0 shadow-sm"
            >
              <Icon className="w-3 h-3 text-indigo-400" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Input Box */}
      <div className="relative glass-panel rounded-2xl p-2 border border-slate-700/80 shadow-2xl focus-within:border-indigo-500/60 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe what you want to purchase (e.g. 'I need 10 laptops for backend devs before Sept 1')..."
          disabled={isLoading || disabled}
          rows={1}
          className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm p-3 pr-24 focus:outline-none resize-none min-h-[44px] max-h-[160px]"
        />

        <div className="absolute right-3 bottom-3 flex items-center gap-2">
          <span className="hidden sm:flex items-center gap-0.5 text-[10px] text-slate-500 font-mono">
            <span>Press</span>
            <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">Enter ↵</kbd>
          </span>

          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading || disabled}
            className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center shadow-md shadow-indigo-600/30 transition-all active:scale-95"
            title="Send Message"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
