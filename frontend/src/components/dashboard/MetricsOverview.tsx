import { AnalyticsOverview } from '../../types';

interface Props {
  data: AnalyticsOverview;
}

const cards = [
  { key: 'total_sessions', label: 'Total Sessions', icon: '&#128172;', color: 'blue' },
  { key: 'messages_today', label: 'Messages Today', icon: '&#128172;', color: 'green' },
  { key: 'unique_users_7d', label: 'Users (7 Days)', icon: '&#128100;', color: 'purple' },
  { key: 'crisis_alerts', label: 'Crisis Alerts', icon: '&#9888;', color: 'red' },
] as const;

const colorMap: Record<string, string> = {
  blue: 'bg-blue-50 border-blue-200 text-blue-700',
  green: 'bg-green-50 border-green-200 text-green-700',
  purple: 'bg-purple-50 border-purple-200 text-purple-700',
  red: 'bg-red-50 border-red-200 text-red-700',
};

export default function MetricsOverview({ data }: Props) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card) => (
        <div key={card.key} className={`${colorMap[card.color]} border rounded-xl p-4`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium opacity-75">{card.label}</span>
            <span className="text-xl" dangerouslySetInnerHTML={{ __html: card.icon }} />
          </div>
          <p className="text-3xl font-bold">{data[card.key].toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
}
