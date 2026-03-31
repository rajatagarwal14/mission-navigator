import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { TopQuestion } from '../../types';

interface Props {
  data: TopQuestion[];
}

export default function TopQuestionsChart({ data }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    question: d.question.length > 40 ? d.question.substring(0, 40) + '...' : d.question,
  }));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h3 className="font-bold text-gray-800 mb-4">Top Questions</h3>
      {data.length === 0 ? (
        <p className="text-gray-400 text-sm text-center py-8">No data yet</p>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={formatted} layout="vertical" margin={{ left: 120 }}>
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="question" tick={{ fontSize: 11 }} width={120} />
            <Tooltip />
            <Bar dataKey="count" fill="#2E75B6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
