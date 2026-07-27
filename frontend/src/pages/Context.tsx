import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { Search, Brain, User, Briefcase, Heart, MessageSquare, Target, AlertCircle } from 'lucide-react'

const typeIcons: Record<string, any> = {
  expertise: Briefcase, interest: Heart, communication_style: MessageSquare, goal: Target, value: Heart, industry: Briefcase,
}
const typeColors: Record<string, string> = {
  expertise: 'text-blue-400 bg-blue-400/10', interest: 'text-green-400 bg-green-400/10',
  communication_style: 'text-amber-400 bg-amber-400/10', goal: 'text-purple-400 bg-purple-400/10',
  value: 'text-pink-400 bg-pink-400/10', industry: 'text-cyan-400 bg-cyan-400/10',
}
const memoryTypeColors: Record<string, string> = {
  fact: 'bg-blue-500/10 text-blue-400', preference: 'bg-green-500/10 text-green-400',
  project: 'bg-purple-500/10 text-purple-400', learning: 'bg-amber-500/10 text-amber-400',
  professional: 'bg-cyan-500/10 text-cyan-400',
}

export default function Context() {
  const [memories, setMemories] = useState<any[]>([])
  const [identity, setIdentity] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [tab, setTab] = useState<'memories' | 'identity'>('memories')
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.get('/context/memories').catch((e) => { console.error(e); return [] }),
      api.get('/context/identity').catch((e) => { console.error(e); return [] }),
    ]).then(([m, i]) => { setMemories(m || []); setIdentity(i || []) })
    .finally(() => setLoading(false))
  }, [])

  const handleSemanticSearch = async () => {
    if (!query.trim()) { setSearchResults(null); return }
    setError('')
    try {
      const resp = await api.post('/context/query', { query, limit: 10 })
      setSearchResults(resp.results || [])
    } catch (e: any) {
      setError('Search failed: ' + (e.message || 'Unknown error'))
      setSearchResults([])
    }
  }

  const displayedMemories = searchResults || (search ? memories.filter(m => m.content.toLowerCase().includes(search.toLowerCase())) : memories)

  if (loading) return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" /></div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Your Context</h1>
        <p className="text-gray-500">Everything the system knows about you</p>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input className="input pl-10" placeholder="Search memories..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="flex gap-2">
          <input className="input w-64" placeholder="Semantic search..." value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSemanticSearch()} />
          <button onClick={handleSemanticSearch} className="btn-primary">Search</button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
          <AlertCircle size={16} className="flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="flex gap-1 rounded-lg bg-gray-900 p-1">
        {(['memories', 'identity'] as const).map(t => (
          <button key={t} onClick={() => { setTab(t); setSearchResults(null) }}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${tab === t ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-300'}`}>
            {t === 'memories' ? `Memories (${memories.length})` : `Identity (${identity.length})`}
          </button>
        ))}
      </div>

      {tab === 'memories' && (
        <div className="space-y-3">
          {searchResults && <p className="text-sm text-gray-500">Semantic search results for "{query}"</p>}
          {displayedMemories.length === 0 ? (
            <div className="card text-center text-gray-500 py-12">
              <Brain size={48} className="mx-auto mb-4 text-gray-700" />
              <p>No memories yet. Connect your accounts or add journal entries to start building context.</p>
            </div>
          ) : displayedMemories.map(m => (
            <div key={m.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`badge ${memoryTypeColors[m.type] || 'bg-gray-500/10 text-gray-400'}`}>{m.type}</span>
                    <span className="text-xs text-gray-600">{m.source}</span>
                  </div>
                  <p className="text-sm text-gray-300 line-clamp-3">{m.content}</p>
                  {m.tags?.length > 0 && (
                    <div className="mt-2 flex gap-1.5 flex-wrap">
                      {m.tags.map((t: string) => <span key={t} className="badge bg-gray-800 text-gray-400">{t}</span>)}
                    </div>
                  )}
                </div>
                <div className="text-right text-xs text-gray-600 ml-4">
                  <div>Importance: {((m.importance ?? 0) * 100).toFixed(0)}%</div>
                  <div>{m.created_at ? new Date(m.created_at).toLocaleDateString() : ''}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'identity' && (
        <div className="space-y-3">
          {identity.length === 0 ? (
            <div className="card text-center text-gray-500 py-12">
              <User size={48} className="mx-auto mb-4 text-gray-700" />
              <p>Identity model will be built as the system gathers more context about you.</p>
            </div>
          ) : identity.map(n => {
            const Icon = typeIcons[n.type] || Brain
            const color = typeColors[n.type] || 'text-gray-400 bg-gray-400/10'
            return (
              <div key={n.id} className="card">
                <div className="flex items-start gap-4">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
                    <Icon size={18} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{n.name}</span>
                      <span className="badge bg-gray-800 text-gray-500">{n.type}</span>
                    </div>
                    {n.data?.description && <p className="mt-1 text-sm text-gray-400">{n.data.description}</p>}
                    {n.data?.evidence && <p className="mt-1 text-xs text-gray-600">Evidence: {n.data.evidence}</p>}
                  </div>
                  <div className="text-xs text-gray-600">{((n.confidence ?? 0) * 100).toFixed(0)}% confidence</div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
