import { useState } from 'react';
import { Settings, Database, Cpu, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../services/api';
import { useQuery } from '@tanstack/react-query';

export function SettingsPage() {
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30000,
  });

  const handleTestAI = async () => {
    try {
      const result = await api.testAI();
      setTestResult(result ? 'success' : 'error');
    } catch {
      setTestResult('error');
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Settings size={24} />
          Settings
        </h1>
        <p className="text-[#a0a0a0] mt-1">Configure your AI coworker</p>
      </div>

      <div className="space-y-6">
        {/* System Status */}
        <div className="bg-[#141414] rounded-xl p-6 border border-[#2a2a2a]">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Database size={18} />
            System Status
          </h2>
          <div className="space-y-3">
            <StatusRow
              label="API Server"
              status={health?.status === 'ok' ? 'ok' : 'error'}
            />
            <StatusRow
              label="Ollama (Local AI)"
              status={health?.checks?.ollama === 'ok' ? 'ok' : 'unavailable'}
            />
            <StatusRow
              label="Redis Cache"
              status={health?.checks?.redis === 'ok' ? 'ok' : 'unavailable'}
            />
          </div>
        </div>

        {/* AI Configuration */}
        <div className="bg-[#141414] rounded-xl p-6 border border-[#2a2a2a]">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Cpu size={18} />
            AI Configuration
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-[#a0a0a0] mb-2">Provider</label>
              <select className="w-full px-4 py-2 bg-[#1f1f1f] border border-[#2a2a2a] rounded-lg text-white">
                <option value="ollama">Ollama (Local, Free)</option>
                <option value="openai">OpenAI</option>
                <option value="openrouter">OpenRouter</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-[#a0a0a0] mb-2">Model</label>
              <input
                type="text"
                defaultValue="llama3.1:8b"
                className="w-full px-4 py-2 bg-[#1f1f1f] border border-[#2a2a2a] rounded-lg text-white"
              />
            </div>
            <button
              onClick={handleTestAI}
              className="px-4 py-2 bg-[#1f1f1f] border border-[#2a2a2a] rounded-lg hover:bg-[#2a2a2a] transition-colors"
            >
              Test Connection
            </button>
            {testResult && (
              <div
                className={`flex items-center gap-2 text-sm ${
                  testResult === 'success' ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {testResult === 'success' ? (
                  <CheckCircle size={16} />
                ) : (
                  <XCircle size={16} />
                )}
                {testResult === 'success' ? 'Connection successful' : 'Connection failed'}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusRow({ label, status }: { label: string; status: string }) {
  const colors = {
    ok: 'bg-green-500',
    error: 'bg-red-500',
    unavailable: 'bg-yellow-500',
  };

  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm">{label}</span>
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${colors[status as keyof typeof colors] || colors.unavailable}`} />
        <span className="text-xs text-[#666] capitalize">{status}</span>
      </div>
    </div>
  );
}
