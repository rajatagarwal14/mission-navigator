import { ChatResponse, ResourceInfo } from '../types';
import { apiFetch } from './client';

export async function sendMessage(sessionId: string, message: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, message, source: 'widget' }),
  });
}

export interface StreamCallbacks {
  onToken: (token: string) => void;
  onResources: (resources: ResourceInfo[]) => void;
  onCrisis: (message: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

export function streamMessage(sessionId: string, message: string, callbacks: StreamCallbacks): () => void {
  const params = new URLSearchParams({
    session_id: sessionId,
    message,
    source: 'widget',
  });

  const eventSource = new EventSource(`/api/chat/stream?${params}`);
  let aborted = false;

  eventSource.addEventListener('token', (e) => {
    if (!aborted) callbacks.onToken(e.data);
  });

  eventSource.addEventListener('resources', (e) => {
    if (!aborted) {
      try {
        const resources = JSON.parse(e.data);
        callbacks.onResources(resources);
      } catch {}
    }
  });

  eventSource.addEventListener('crisis', (e) => {
    if (!aborted) callbacks.onCrisis(e.data);
  });

  eventSource.addEventListener('done', () => {
    if (!aborted) {
      callbacks.onDone();
      eventSource.close();
    }
  });

  eventSource.onerror = () => {
    if (!aborted) {
      callbacks.onError('Connection lost. Please try again.');
      eventSource.close();
    }
  };

  return () => {
    aborted = true;
    eventSource.close();
  };
}

export async function logResourceClick(sessionId: string, resourceName: string, resourceUrl?: string) {
  const params = new URLSearchParams({ session_id: sessionId, resource_name: resourceName });
  if (resourceUrl) params.set('resource_url', resourceUrl);
  await fetch(`/api/admin/analytics/resource-click?${params}`, { method: 'POST' }).catch(() => {});
}
