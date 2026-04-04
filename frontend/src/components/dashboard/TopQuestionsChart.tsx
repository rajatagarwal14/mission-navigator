import { TopQuestion } from '../../types';

interface Props {
  data: TopQuestion[];
}

export default function TopQuestionsChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="font-bold text-gray-800 mb-4">Top Questions</h3>
        <p className="text-gray-400 text-sm text-center py-8">No data yet</p>
      </div>
    );
  }

  const max = Math.max(...data.map((d) => d.count));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h3 className="font-bold text-gray-800 mb-4">Top Questions</h3>
      <div className="space-y-2">
        {data.map((item, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-6 text-xs text-gray-400 text-right shrink-0">{i + 1}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-sm text-gray-700 truncate pr-2 capitalize">
                  {item.question}
                </span>
                <span className="text-sm font-semibold text-[#2E75B6] shrink-0">{item.count}</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div
                  className="bg-[#2E75B6] h-2 rounded-full transition-all"
                  style={{ width: `${(item.count / max) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
