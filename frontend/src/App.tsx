import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { ChatWindow } from './components/ChatWindow';
import { ChatInput } from './components/ChatInput';
import { ChatMessage, UserContext } from './types/chat';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [threadId] = useState<string>(`thread_${Math.random().toString(36).substring(2, 11)}`);
  const [currentPhase, setCurrentPhase] = useState<'Clarification' | 'Demand' | 'GeneratePR' | 'Completed'>('Clarification');

  // Demo user context
  const [userContext] = useState<UserContext>({
    userId: 'usr_pras',
    userName: 'Prasetyo Suhada',
    departmentId: 'DEPT-ENG',
    costCenter: 'CC-ENG-001'
  });

  const handleSendMessage = (content: string) => {
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Mock UI transition response for Task 4.1 (Full API integration in Task 4.2)
    setTimeout(() => {
      let agentReply = '';
      if (content.toLowerCase().includes('laptop')) {
        agentReply = "I understand you need laptops. Could you please specify how many units are required and for what workload?";
        setCurrentPhase('Clarification');
      } else if (content.toLowerCase().includes('10')) {
        agentReply = "📊 **Demand Analysis Complete**\n\n• **Requested Quantity:** 10\n• **Warehouse Stock:** 3 units\n• **Unused Assets:** 5 units\n• **Recommended Purchase Quantity:** **2 units**\n\n**Justification:** Deducting 8 existing units (3 warehouse + 5 assets), 2 new units are recommended.\n\nProceeding to generate Purchase Requisition draft...";
        setCurrentPhase('Demand');
      } else {
        agentReply = `I have received your request: "${content}". Please let me know the quantity and target delivery date so I can verify our enterprise inventory.`;
      }

      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_ai`,
        role: 'assistant',
        content: agentReply,
        timestamp: new Date().toISOString(),
        agentName: currentPhase === 'Demand' ? 'Demand Analysis Agent' : 'Clarification Agent'
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 600);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar userContext={userContext} currentPhase={currentPhase} threadId={threadId} />

      {/* Main Conversation Stream */}
      <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <ChatWindow messages={messages} isLoading={isLoading} />
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </main>
    </div>
  );
};

export default App;
