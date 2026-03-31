import { useState, useEffect } from 'react';
import { AnalyticsDashboard } from '../types';
import { getDashboard } from '../api/admin';
import MetricsOverview from '../components/dashboard/MetricsOverview';
import UsageTrend from '../components/dashboard/UsageTrend';
import TopQuestionsChart from '../components/dashboard/TopQuestionsChart';
import TopResourcesTable from '../components/dashboard/TopResourcesTable';

export default function DashboardPage() {
  const [data, setData] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    setLoading(true);
    getDashboard(days).then(setData).catch(console.error).finally(() => setLoading(false));
  }, [days]);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-[#1B2A4A]">Analytics Dashboard</h2>
        <div className="flex gap-2">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-lg text-sm ${
                days === d ? 'bg-[#1B2A4A] text-white' : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      <MetricsOverview data={data.overview} />
      <UsageTrend data={data.usage_trend} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TopQuestionsChart data={data.top_questions} />
        <TopResourcesTable data={data.top_resources} />
      </div>
    </div>
  );
}
