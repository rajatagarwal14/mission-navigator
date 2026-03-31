export default function CrisisAlert() {
  return (
    <div className="crisis-pulse bg-red-600 text-white px-4 py-3 rounded-lg mx-4 mt-2 flex items-start gap-3">
      <span className="text-2xl flex-shrink-0">&#9888;</span>
      <div className="text-sm">
        <p className="font-bold mb-1">If you are in crisis, please reach out now:</p>
        <p>
          <strong>Veterans Crisis Line:</strong> Call{' '}
          <a href="tel:988" className="underline font-bold text-white">988</a> (press 1) |
          Text <strong>838255</strong> |{' '}
          <a href="https://www.veteranscrisisline.net" target="_blank" rel="noopener" className="underline text-white">Chat Online</a>
        </p>
        <p className="mt-1">
          <strong>Road Home Program:</strong>{' '}
          <a href="tel:3129428387" className="underline text-white">(312) 942-8387</a>
        </p>
      </div>
    </div>
  );
}
