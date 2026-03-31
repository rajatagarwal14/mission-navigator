import { ChatMessage } from '../../types';
import ResourceCard from './ResourceCard';
import CrisisAlert from './CrisisAlert';

interface Props {
  message: ChatMessage;
  sessionId: string;
}

function renderMarkdown(text: string) {
  // Simple markdown rendering: bold, links, lists
  let html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener" class="text-blue-600 underline">$1</a>')
    .replace(/^- (.*)/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.*)/gm, '<li>$2</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>');

  // Wrap consecutive <li> in <ul>
  html = html.replace(/((?:<li>.*?<\/li>\s*)+)/g, '<ul class="list-disc ml-4 my-1">$1</ul>');

  return `<p>${html}</p>`;
}

export default function MessageBubble({ message, sessionId }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-[#1B2A4A] flex items-center justify-center text-white text-sm font-bold flex-shrink-0 mr-2 mt-1">
          MN
        </div>
      )}
      <div className={`max-w-[80%] ${isUser ? 'order-1' : ''}`}>
        {message.isCrisis && <CrisisAlert />}

        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? 'bg-[#2E75B6] text-white rounded-br-md'
              : 'bg-white border border-gray-200 text-gray-800 rounded-bl-md shadow-sm'
          }`}
        >
          <div
            className="message-content"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
          />
          {message.isStreaming && !message.content && (
            <div className="flex gap-1 py-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}
          {message.isStreaming && message.content && (
            <span className="typing-cursor inline-block w-0.5 h-4 bg-gray-600 ml-0.5 align-middle" />
          )}
        </div>

        {Array.isArray(message.resources) && message.resources.length > 0 && !message.isStreaming && (
          <div className="mt-2 grid gap-2">
            {message.resources.map((r, i) => (
              <ResourceCard key={i} resource={r} sessionId={sessionId} />
            ))}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-[#C5922E] flex items-center justify-center text-white text-sm font-bold flex-shrink-0 ml-2 mt-1">
          You
        </div>
      )}
    </div>
  );
}
