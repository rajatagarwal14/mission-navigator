import { useRef, useEffect } from 'react';
import { useChat } from '../../hooks/useChat';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import WelcomeScreen from './WelcomeScreen';

interface Props {
  fullPage?: boolean;
  onMinimize?: () => void;
}

export default function ChatWindow({ fullPage = false, onMinimize }: Props) {
  const { messages, isLoading, error, sendMessage, clearChat, sessionId } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const containerClass = fullPage
    ? 'flex flex-col h-screen bg-gray-50'
    : 'flex flex-col h-[600px] w-[400px] bg-gray-50 rounded-2xl shadow-2xl border border-gray-200 overflow-hidden';

  return (
    <div className={containerClass}>
      {/* Header */}
      <div className="bg-[#1B2A4A] text-white px-4 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
            <span className="text-lg font-bold">MN</span>
          </div>
          <div>
            <h1 className="font-bold text-sm">Mission Navigator</h1>
            <p className="text-xs text-blue-200">Road Home Program Resource Assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="text-xs text-blue-200 hover:text-white px-2 py-1 rounded hover:bg-white/10 transition-colors"
              title="Start new conversation"
            >
              New Chat
            </button>
          )}
          {onMinimize && (
            <button onClick={onMinimize} className="text-blue-200 hover:text-white p-1" title="Minimize">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="4 14 10 14 10 20" /><polyline points="20 10 14 10 14 4" />
                <line x1="14" y1="10" x2="21" y2="3" /><line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      {messages.length === 0 ? (
        <WelcomeScreen onSuggestedClick={sendMessage} />
      ) : (
        <div className="flex-1 overflow-y-auto chat-messages p-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} sessionId={sessionId} />
          ))}
          {error && (
            <div className="text-center text-sm text-red-500 bg-red-50 rounded-lg p-2 mb-2">
              {error}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Input */}
      <MessageInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
