interface Props {
  onSuggestedClick: (question: string) => void;
}

const SUGGESTED_QUESTIONS = [
  "What services does the Road Home Program offer?",
  "How can I get help for my family?",
  "Are services available outside of Illinois?",
  "What mental health resources are available for free?",
];

export default function WelcomeScreen({ onSuggestedClick }: Props) {
  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="text-center max-w-lg">
        <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-[#1B2A4A] flex items-center justify-center">
          <span className="text-3xl text-white font-bold">MN</span>
        </div>
        <h2 className="text-2xl font-bold text-[#1B2A4A] mb-2">Welcome to Mission Navigator</h2>
        <p className="text-gray-600 mb-6 text-sm leading-relaxed">
          I'm here to help you find mental health services and resources through the
          Road Home Program at Rush University Medical Center. Ask me anything about
          available services, eligibility, or how to get started.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {SUGGESTED_QUESTIONS.map((q, i) => (
            <button
              key={i}
              onClick={() => onSuggestedClick(q)}
              className="text-left text-sm border border-blue-200 rounded-xl px-4 py-3 hover:bg-blue-50 hover:border-blue-300 transition-colors text-gray-700"
            >
              {q}
            </button>
          ))}
        </div>

        <div className="mt-6 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            If you are in crisis, call the <strong>Veterans Crisis Line: 988</strong> (press 1) or
            text <strong>838255</strong>
          </p>
        </div>
      </div>
    </div>
  );
}
