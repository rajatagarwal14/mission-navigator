import { TopResource } from '../../types';

interface Props {
  data: TopResource[];
}

export default function TopResourcesTable({ data }: Props) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h3 className="font-bold text-gray-800 mb-4">Top Resources</h3>
      {data.length === 0 ? (
        <p className="text-gray-400 text-sm text-center py-8">No data yet</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-2 px-2 font-medium text-gray-500">Resource</th>
                <th className="text-right py-2 px-2 font-medium text-gray-500">Citations</th>
                <th className="text-right py-2 px-2 font-medium text-gray-500">Clicks</th>
              </tr>
            </thead>
            <tbody>
              {data.map((r, i) => (
                <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2 px-2 text-gray-800">{r.name}</td>
                  <td className="py-2 px-2 text-right text-blue-600 font-medium">{r.citations}</td>
                  <td className="py-2 px-2 text-right text-green-600 font-medium">{r.clicks}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
