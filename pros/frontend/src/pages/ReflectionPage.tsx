import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { MessageSquare, Send, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export function ReflectionPage() {
  const [responses, setResponses] = useState<Record<number, string>>({});

  const { data: questionsData, isLoading, refetch } = useQuery({
    queryKey: ['reflection-questions'],
    queryFn: () => api.getReflectionQuestions(),
  });

  const submitMutation = useMutation({
    mutationFn: (data: any) => api.submitReflection(data),
    onSuccess: () => {
      setResponses({});
      refetch();
    },
  });

  const questions = questionsData?.questions || [];

  const handleSubmit = () => {
    const filledResponses = questions
      .map((q: any, i: number) => ({
        question: q.question,
        answer: responses[i] || '',
      }))
      .filter((r: any) => r.answer.trim());

    if (filledResponses.length > 0) {
      submitMutation.mutate({ responses: filledResponses });
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <MessageSquare size={24} />
          Daily Reflection
        </h1>
        <p className="text-[#a0a0a0] mt-1">
          Answer a few questions to help your AI coworker understand your work
        </p>
      </div>

      <div className="mb-4">
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 text-sm text-[#a0a0a0] hover:text-white transition-colors"
        >
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          Generate new questions
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-[#666]">Generating questions...</div>
      ) : (
        <div className="space-y-6">
          {questions.map((q: any, i: number) => (
            <div key={i} className="bg-[#141414] rounded-xl p-5 border border-[#2a2a2a]">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold mt-1">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <p className="font-medium mb-3">{q.question}</p>
                  <textarea
                    value={responses[i] || ''}
                    onChange={(e) =>
                      setResponses({ ...responses, [i]: e.target.value })
                    }
                    placeholder="Your answer..."
                    className="w-full px-4 py-3 bg-[#1f1f1f] border border-[#2a2a2a] rounded-lg text-white placeholder-[#666] h-24 resize-none focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          ))}

          {questions.length > 0 && (
            <button
              onClick={handleSubmit}
              disabled={submitMutation.isPending || Object.values(responses).every(v => !v?.trim())}
              className="w-full py-3 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Send size={16} />
              {submitMutation.isPending ? 'Processing...' : 'Submit Reflection'}
            </button>
          )}

          {submitMutation.isSuccess && (
            <div className="p-4 bg-green-900/30 border border-green-800 rounded-lg text-green-400 text-sm">
              Reflection processed! New memories have been created.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
