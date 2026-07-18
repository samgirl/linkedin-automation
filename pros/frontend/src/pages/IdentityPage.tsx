import { useQuery } from '@tanstack/react-query';
import { Users, Briefcase, Code, Target, Lightbulb } from 'lucide-react';
import { api } from '../services/api';

export function IdentityPage() {
  const { data: identity, isLoading } = useQuery({
    queryKey: ['identity'],
    queryFn: () => api.getIdentity(),
  });

  const nodesByType = (type: string) =>
    identity?.nodes?.filter((n: any) => n.type === type) || [];

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Users size={24} />
          Identity
        </h1>
        <p className="text-[#a0a0a0] mt-1">Your professional identity graph</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-[#666]">Loading identity...</div>
      ) : (
        <div className="space-y-6">
          {/* Projects */}
          <IdentitySection
            icon={<Briefcase size={20} />}
            title="Projects"
            nodes={nodesByType('project')}
            emptyText="No projects tracked yet"
          />

          {/* Skills */}
          <IdentitySection
            icon={<Code size={20} />}
            title="Skills"
            nodes={nodesByType('skill')}
            emptyText="No skills identified yet"
          />

          {/* Topics */}
          <IdentitySection
            icon={<Lightbulb size={20} />}
            title="Topics"
            nodes={nodesByType('topic')}
            emptyText="No topics tracked yet"
          />

          {/* Goals */}
          <IdentitySection
            icon={<Target size={20} />}
            title="Goals"
            nodes={nodesByType('goal')}
            emptyText="No goals set yet"
          />
        </div>
      )}
    </div>
  );
}

function IdentitySection({
  icon,
  title,
  nodes,
  emptyText,
}: {
  icon: React.ReactNode;
  title: string;
  nodes: any[];
  emptyText: string;
}) {
  return (
    <div className="bg-[#141414] rounded-xl p-6 border border-[#2a2a2a]">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        {icon}
        {title}
        <span className="text-sm text-[#666] font-normal ml-auto">
          {nodes.length} items
        </span>
      </h2>
      
      {nodes.length === 0 ? (
        <p className="text-sm text-[#666]">{emptyText}</p>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {nodes.map((node: any) => (
            <div
              key={node.id}
              className="p-3 bg-[#1f1f1f] rounded-lg hover:bg-[#2a2a2a] transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">{node.name}</span>
                <span className="text-xs text-[#666]">
                  {Math.round(node.confidence * 100)}%
                </span>
              </div>
              {node.data?.description && (
                <p className="text-xs text-[#a0a0a0] mt-1">{node.data.description}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
