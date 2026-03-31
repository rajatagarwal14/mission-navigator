import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { UsageTrendPoint } from '../../types';

interface Props {
  data: UsageTrendPoint[];
}

export default function UsageTrend({ data }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  }));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
      <h3 className="font-bold text-gray-800 mb-4">Usage Trend</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="sessions" stroke="#2E75B6" strokeWidth={2} name="Sessions" />
          <Line type="monotone" dataKey="messages" stroke="#C5922E" strokeWidth={2} name="Messages" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
