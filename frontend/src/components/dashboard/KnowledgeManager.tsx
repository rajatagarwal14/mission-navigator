import { useState, useEffect } from 'react';
import { KnowledgeDocument } from '../../types';
import { getKnowledgeDocuments, createKnowledgeDocument, updateKnowledgeDocument, deleteKnowledgeDocument } from '../../api/admin';

const CATEGORIES = [
  'Mental Health', 'Child & Youth', 'Caregiver Support', 'Illinois-Specific',
  'Financial & Practical', 'Educational Support', 'LGBTQ+ Resources', 'Crisis Support',
  'Comprehensive Support', 'Healthcare', 'Employment', 'Wellness', 'Road Home Program',
];

export default function KnowledgeManager() {
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<KnowledgeDocument | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ title: '', category: 'Mental Health', content: '', url: '', phone: '' });

  const load = async () => {
    setLoading(true);
    try {
      const data = await getKnowledgeDocuments();
      setDocs(data.documents);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    try {
      if (editing) {
        await updateKnowledgeDocument(editing.id, form);
      } else {
        await createKnowledgeDocument(form);
      }
      setCreating(false);
      setEditing(null);
      setForm({ title: '', category: 'Mental Health', content: '', url: '', phone: '' });
      load();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this document? This cannot be undone.')) return;
    await deleteKnowledgeDocument(id);
    load();
  };

  const startEdit = (doc: KnowledgeDocument) => {
    setEditing(doc);
    setCreating(true);
    setForm({ title: doc.title, category: doc.category, content: doc.content, url: doc.url || '', phone: doc.phone || '' });
  };

  if (creating) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-bold text-gray-800 mb-4">{editing ? 'Edit Document' : 'Add Document'}</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
            <textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} rows={8} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
              <input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="https://..." />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="1-800-..." />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleSave} className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm hover:bg-[#2E75B6]">Save</button>
            <button onClick={() => { setCreating(false); setEditing(null); }} className="border border-gray-300 px-4 py-2 rounded-lg text-sm hover:bg-gray-50">Cancel</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-gray-800">Knowledge Base ({docs.length} documents)</h3>
        <button onClick={() => setCreating(true)} className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm hover:bg-[#2E75B6]">
          + Add Document
        </button>
      </div>
      {loading ? (
        <div className="text-center py-8 text-gray-400">Loading...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-2 px-2 font-medium text-gray-500">Title</th>
                <th className="text-left py-2 px-2 font-medium text-gray-500">Category</th>
                <th className="text-center py-2 px-2 font-medium text-gray-500">Chunks</th>
                <th className="text-left py-2 px-2 font-medium text-gray-500">Source</th>
                <th className="text-right py-2 px-2 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((doc) => (
                <tr key={doc.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2 px-2 text-gray-800 font-medium">{doc.title}</td>
                  <td className="py-2 px-2"><span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{doc.category}</span></td>
                  <td className="py-2 px-2 text-center text-gray-500">{doc.chunks_count}</td>
                  <td className="py-2 px-2 text-gray-500 text-xs">{doc.source}</td>
                  <td className="py-2 px-2 text-right">
                    <button onClick={() => startEdit(doc)} className="text-blue-600 hover:underline text-xs mr-2">Edit</button>
                    <button onClick={() => handleDelete(doc.id)} className="text-red-600 hover:underline text-xs">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
