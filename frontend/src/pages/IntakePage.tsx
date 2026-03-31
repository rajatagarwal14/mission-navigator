import { useState, useRef, useEffect } from 'react';
import { apiFetch } from '../api/client';
import { IntakeResponse } from '../types';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function IntakePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [intakeId, setIntakeId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [complete, setComplete] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Start intake session
    apiFetch<IntakeResponse>('/intake/start', { method: 'POST', body: JSON.stringify({}) })
      .then((res) => {
        setIntakeId(res.intake_id);
        setMessages([{ role: 'assistant', content: res.message }]);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || !intakeId || loading) return;
    const text = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setLoading(true);

    try {
      const res = await apiFetch<IntakeResponse>('/intake/message', {
        method: 'POST',
        body: JSON.stringify({ intake_id: intakeId, message: text }),
      });
      setMessages((prev) => [...prev, { role: 'assistant', content: res.message }]);
      if (res.is_complete) setComplete(true);
    } catch (e: any) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Something went wrong. Please try again.' }]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-[#1B2A4A] text-white px-4 py-3 flex items-center gap-3 flex-shrink-0">
        <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
          <span className="text-lg font-bold">MN</span>
        </div>
        <div>
          <h1 className="font-bold text-sm">Road Home Program Intake</h1>
          <p className="text-xs text-blue-200">Confidential - Information shared only with intake team</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 max-w-2xl mx-auto w-full">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#2E75B6] text-white rounded-br-md'
                  : 'bg-white border border-gray-200 text-gray-800 rounded-bl-md shadow-sm'
              }`}
              dangerouslySetInnerHTML={{
                __html: msg.content
                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  .replace(/\n/g, '<br/>'),
              }}
            />
          </div>
        ))}
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      {!complete && (
        <div className="border-t border-gray-200 bg-white p-3">
          <div className="flex items-end gap-2 max-w-2xl mx-auto">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Type your response..."
              disabled={loading}
              className="flex-1 rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
            <button onClick={sendMessage} disabled={loading || !input.trim()} className="bg-[#1B2A4A] text-white rounded-xl px-4 py-2.5 text-sm font-medium disabled:bg-gray-300">
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
