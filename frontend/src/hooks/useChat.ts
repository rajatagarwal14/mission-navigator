import { useState, useCallback, useRef } from 'react';
import { ChatMessage, ResourceInfo } from '../types';
import { streamMessage } from '../api/chat';

function generateId(): string {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

function getSessionId(): string {
  let id = localStorage.getItem('mn_session_id');
  if (!id) {
    id = generateId();
    localStorage.setItem('mn_session_id', id);
  }
  return id;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionId = useRef(getSessionId());
  const cancelRef = useRef<(() => void) | null>(null);

  const sendMessage = useCallback((text: string) => {
    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    const assistantMsg: ChatMessage = {
      id: generateId(),
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);
    setError(null);

    const cancel = streamMessage(sessionId.current, text, {
      onToken: (token) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, content: last.content + token };
          }
          return updated;
        });
      },
      onResources: (resources: ResourceInfo[]) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, resources };
          }
          return updated;
        });
      },
      onCrisis: (message: string) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, content: message, isCrisis: true, isStreaming: false };
          }
          return updated;
        });
        setIsLoading(false);
      },
      onDone: () => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, isStreaming: false };
          }
          return updated;
        });
        setIsLoading(false);
      },
      onError: (errorMsg: string) => {
        setError(errorMsg);
        setIsLoading(false);
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === 'assistant' && !last.content) {
            updated.pop();
          }
          return updated;
        });
      },
    });

    cancelRef.current = cancel;
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    const newId = generateId();
    sessionId.current = newId;
    localStorage.setItem('mn_session_id', newId);
  }, []);

  return { messages, isLoading, error, sendMessage, clearChat, sessionId: sessionId.current };
}
