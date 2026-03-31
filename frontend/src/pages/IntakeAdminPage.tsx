import { useState, useEffect } from 'react';
import { getIntakeSubmissions } from '../api/admin';

interface Submission {
  id: string;
  summary: string;
  consent_given: boolean;
  submitted_at: string;
  reviewed: boolean;
  created_at: string;
}

export default function IntakeAdminPage() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    getIntakeSubmissions()
      .then((data: any) => setSubmissions(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold text-[#1B2A4A] mb-6">Intake Submissions</h2>
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        {loading ? (
          <div className="text-center py-8 text-gray-400">Loading...</div>
        ) : submissions.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p className="text-lg mb-2">No submissions yet</p>
            <p className="text-sm">Intake submissions will appear here when veterans complete the intake process.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {submissions.map((s) => (
              <div key={s.id} className="border border-gray-100 rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpanded(expanded === s.id ? null : s.id)}
                  className="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <span className={`w-2 h-2 rounded-full ${s.reviewed ? 'bg-green-400' : 'bg-yellow-400'}`} />
                    <span className="text-sm font-medium text-gray-800">
                      {new Date(s.submitted_at).toLocaleDateString()} at{' '}
                      {new Date(s.submitted_at).toLocaleTimeString()}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded ${s.consent_given ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                      {s.consent_given ? 'Consent Given' : 'No Consent'}
                    </span>
                  </div>
                  <span className="text-gray-400">{expanded === s.id ? '[-]' : '[+]'}</span>
                </button>
                {expanded === s.id && (
                  <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
                    <div
                      className="text-sm text-gray-700 whitespace-pre-wrap"
                      dangerouslySetInnerHTML={{
                        __html: s.summary
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\n/g, '<br/>'),
                      }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
