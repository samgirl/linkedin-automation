import { useQuery } from '@tanstack/react-query';
import { Brain, FileText, Users, TrendingUp, Clock, Zap } from 'lucide-react';
import { api } from '../services/api';

export function Dashboard() {
  const { data: events } = useQuery({
    queryKey: ['events'],
    queryFn: () => api.getEvents({ limit: 10 }),
  });

  const { data: memories } = useQuery({
    queryKey: ['memories'],
    queryFn: () => api.getMemories({ limit: 10 }),
  });

  const { data: identity } = useQuery({
    queryKey: ['identity'],
    queryFn: () => api.getIdentity(),
  });

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Good morning</h1>
        <p className="text-[#a0a0a0] mt-1">Your AI coworker has been working while you slept.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Brain className="text-blue-500" />}
          label="Memories"
          value={memories?.total || 0}
        />
        <StatCard
          icon={<FileText className="text-green-500" />}
          label="Events Today"
          value={events?.total || 0}
        />
        <StatCard
          icon={<Users className="text-purple-500" />}
          label="Identity Nodes"
          value={identity?.nodes?.length || 0}
        />
        <StatCard
          icon={<TrendingUp className="text-orange-500" />}
          label="Topics Tracked"
          value={identity?.nodes?.filter((n: any) => n.type === 'topic')?.length || 0}
        />
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-[#141414] rounded-xl p-6 border border-[#2a2a2a]">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Clock size={18} />
            Recent Events
          </h2>
          <div className="space-y-3">
            {events?.events?.slice(0, 5).map((event: any) => (
              <div key={event.id} className="flex items-start gap-3 p-3 bg-[#1f1f1f] rounded-lg">
                <div className="w-2 h-2 rounded-full bg-blue-500 mt-2" />
                <div>
                  <p className="text-sm font-medium">{event.title || event.type}</p>
                  <p className="text-xs text-[#666] mt-1">
                    {new Date(event.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
            {(!events?.events || events.events.length === 0) && (
              <p className="text-sm text-[#666]">No events yet. Start capturing your work!</p>
            )}
          </div>
        </div>

        <div className="bg-[#141414] rounded-xl p-6 border border-[#2a2a2a]">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Zap size={18} />
            Key Memories
          </h2>
          <div className="space-y-3">
            {memories?.memories?.slice(0, 5).map((memory: any) => (
              <div key={memory.id} className="p-3 bg-[#1f1f1f] rounded-lg">
                <p className="text-sm">{memory.content.slice(0, 100)}...</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs px-2 py-1 bg-[#2a2a2a] rounded">
                    {memory.type}
                  </span>
                  <span className="text-xs text-[#666]">
                    {Math.round(memory.importance * 100)}% important
                  </span>
                </div>
              </div>
            ))}
            {(!memories?.memories || memories.memories.length === 0) && (
              <p className="text-sm text-[#666]">No memories yet. Your context engine is warming up.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="bg-[#141414] rounded-xl p-5 border border-[#2a2a2a]">
      <div className="flex items-center justify-between">
        <div>{icon}</div>
        <span className="text-2xl font-bold">{value}</span>
      </div>
      <p className="text-sm text-[#a0a0a0] mt-2">{label}</p>
    </div>
  );
}
