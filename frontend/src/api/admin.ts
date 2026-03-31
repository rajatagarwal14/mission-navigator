import { AnalyticsDashboard, KnowledgeDocument } from '../types';
import { apiFetch } from './client';

export async function getDashboard(days: number = 30): Promise<AnalyticsDashboard> {
  return apiFetch<AnalyticsDashboard>(`/admin/analytics/dashboard?days=${days}`);
}

export async function getKnowledgeDocuments(): Promise<{ documents: KnowledgeDocument[]; total: number }> {
  return apiFetch('/admin/knowledge');
}

export async function createKnowledgeDocument(doc: {
  title: string;
  category: string;
  content: string;
  url?: string;
  phone?: string;
}): Promise<KnowledgeDocument> {
  return apiFetch('/admin/knowledge', {
    method: 'POST',
    body: JSON.stringify(doc),
  });
}

export async function updateKnowledgeDocument(id: number, doc: Partial<{
  title: string;
  category: string;
  content: string;
  url?: string;
  phone?: string;
}>): Promise<KnowledgeDocument> {
  return apiFetch(`/admin/knowledge/${id}`, {
    method: 'PUT',
    body: JSON.stringify(doc),
  });
}

export async function deleteKnowledgeDocument(id: number): Promise<void> {
  return apiFetch(`/admin/knowledge/${id}`, { method: 'DELETE' });
}

export async function getIntakeSubmissions() {
  return apiFetch('/intake/admin/submissions');
}
