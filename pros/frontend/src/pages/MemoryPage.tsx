import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Plus, Brain } from 'lucide-react';
import { api } from '../services/api';

export function MemoryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const queryClient = useQueryClient();

  const { data: memories, isLoading } = useQuery({
    queryKey: ['memories'],
    queryFn: () => api.getMemories({ limit: 50 }),
  });

  const searchMutation = useMutation({
    mutationFn: (query: string) => api.searchMemories(query),
  });

  const displayMemories = searchMutation.data?.memories || memories?.memories || [];

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain size={24} />
            Memory
          </h1>
          <p className="text-[#a0a0a0] mt-1">Your professional knowledge base</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          Add Memory
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666]" size={18} />
          <input
            type="text"
            placeholder="Search your memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && searchQuery) {
                searchMutation.mutate(searchQuery);
              }
            }}
            className="w-full pl-10 pr-4 py-3 bg-[#1f1f1f] border border-[#2a2a2a] rounded-lg text-white placeholder-[#666] focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* Memory List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="text-center py-12 text-[#666]">Loading memories...</div>
        ) : displayMemories.length === 0 ? (
          <div className="text-center py-12">
            <Brain size={48} className="mx-auto text-[#2a2a2a] mb-4" />
            <p className="text-[#666]">No memories yet</p>
            <p className="text-sm text-[#444] mt-1">
              Start capturing your work and your memory will grow
            </p>
          </div>
        ) : (
          displayMemories.map((memory: any) => (
            <MemoryCard key={memory.id} memory={memory} />
          ))
        )}
      </div>

      {/* Create Modal */}
      {showCreate && <CreateMemoryModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}

function MemoryCard({ memory }: { memory: any }) {
  return (
    <div className="bg-[#141414] rounded-xl p-5 border border-[#2a2a2a] hover:border-[#3a3a3a] transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm leading-relaxed">{memory.content}</p>
          <div className="flex items-center gap-2 mt-3">
            <span className="text-xs px-2 py-1 bg-[#1f1f1f] rounded">
              {memory.type}
            </span>
            {memory.tags?.map((tag: string) => (
              <span key={tag} className="text-xs px-2 py-1 bg-blue-900/30 text-blue-400 rounded">
                {tag}
              </span>
            ))}
          </div>
        </div>
        <div className="text-right ml-4">
          <div className="text-lg font-semibold text-[#a0a0a0]">
            {Math.round(memory.importance * 100)}
          </div>
          <div className="text-xs text-[#666]">importance</div>
        </div>
      </div>
    </div>
  );
}

function CreateMemoryModal({ onClose }: { onClose: () => void }) {
  const [content, setContent] = useState('');
  const [type, setType] = useState('episodic');
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createMemory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] });
      onClose();
    },
  });

  const handleSubmit = () => {
    if (!content.trim()) return;
    createMutation.mutate({ type, content, importance: 0.5, confidence: 0.5 });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#141414] rounded-xl p-6 w-full max-w-lg border border-[#2a2a2a]">
        <h2 className="text-lg font-semibold mb-4">Add Memory</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-[#a0a0a0] mb-2">Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full px-4 py-2 bg-[#1f1f1f] border border-[#2a2a2a] rounded-lg text-white"
            >
              <option value="episodic">Event (what happened)</option>
              <option value="semantic">Knowledge (what you know)</option>
              <option value="belief">Belief (what you believe)</option>
              <option value="idea">Idea (what you're thinking)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-[#a0a0a0] mb-2">Content</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="What do you want to remember?"
              className="w-full px-4 py-3 bg-[#1f1f1f] border border-[#2a2a2a] rounded-lg text-white placeholder-[#666] h-32 resize-none focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
        
        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-[#a0a0a0] hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!content.trim() || createMutation.isPending}
            className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {createMutation.isPending ? 'Saving...' : 'Save Memory'}
          </button>
        </div>
      </div>
    </div>
  );
}
