import { ResourceInfo } from '../../types';
import { logResourceClick } from '../../api/chat';

interface Props {
  resource: ResourceInfo;
  sessionId: string;
}

export default function ResourceCard({ resource, sessionId }: Props) {
  const handleClick = () => {
    logResourceClick(sessionId, resource.name, resource.url);
  };

  return (
    <div className="bg-white border border-blue-100 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-[#1B2A4A] text-sm truncate">{resource.name}</h4>
          <span className="inline-block text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded mt-1">
            {resource.category}
          </span>
        </div>
      </div>
      <div className="mt-2 flex flex-wrap gap-2 text-xs">
        {resource.phone && (
          <a href={`tel:${resource.phone.replace(/\D/g, '')}`} className="flex items-center gap-1 text-green-700 hover:underline" onClick={handleClick}>
            <span>&#128222;</span> {resource.phone}
          </a>
        )}
        {resource.url && (
          <a href={resource.url} target="_blank" rel="noopener" className="flex items-center gap-1 text-blue-600 hover:underline" onClick={handleClick}>
            <span>&#127760;</span> Visit Website
          </a>
        )}
      </div>
    </div>
  );
}
