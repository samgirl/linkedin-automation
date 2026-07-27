import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../hooks/useAuth'
import { Target, Brain, BookOpen, TrendingUp, Sparkles, ArrowRight, Flame, Search, AlertCircle, Plug, Pen } from 'lucide-react'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [briefing, setBriefing] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [trends, setTrends] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [scanningTrends, setScanningTrends] = useState(false)
  const [error, setError] = useState('')
  const [recentEntries, setRecentEntries] = useState<any[]>([])

  useEffect(() => {
    api.get('/auth/onboarding-status').then(r => {
      if (!r.completed) {
        navigate('/onboarding')
        return
      }
    }).catch(() => {})

    Promise.all([
      api.get('/dashboard/briefing').catch(() => null),
      api.get('/dashboard/stats').catch(() => null),
      api.get('/scanner/trends').catch(() => ({ trends: [] })),
      api.get('/journal/?limit=3').catch(() => []),
    ]).then(([b, s, t, entries]) => {
      setBriefing(b)
      setStats(s)
      setTrends(t?.trends || [])
      setRecentEntries(entries || [])
    }).finally(() => setLoading(false))
  }, [])

  const refreshTrends = async () => {
    setScanningTrends(true)
    setError('')
    try {
      const t = await api.get('/scanner/trends')
      setTrends(t?.trends || [])
    } catch (e: any) {
      setError('Failed to load trends: ' + (e.message || 'Unknown error'))
    }
    setScanningTrends(false)
  }

  const hasData = stats && (stats.total_memories > 0 || stats.journal_entries > 0)
  const name = user?.name?.split(' ')[0] || 'there'

  if (loading) return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" /></div>

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Welcome back, {name}</h1>
        <p className="text-gray-500">Here's your daily briefing</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
          <AlertCircle size={16} className="flex-shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError('')} className="text-red-400 hover:text-red-300">&times;</button>
        </div>
      )}

      {!hasData && (
        <div className="card border-brand-600/30 bg-brand-600/5">
          <div className="mb-3 font-semibold text-brand-400">Get Started with PROS</div>
          <p className="mb-4 text-sm text-gray-400">Your dashboard is empty. Here's how to get value from PROS:</p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <button onClick={() => navigate('/journal')} className="flex items-center gap-3 rounded-lg bg-gray-800/50 p-3 text-left transition-colors hover:bg-gray-800">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10 text-purple-400"><Pen size={18} /></div>
              <div><div className="text-sm font-medium">Add a Journal Entry</div><div className="text-xs text-gray-500">Capture what you're working on</div></div>
            </button>
            <button onClick={() => navigate('/opportunities')} className="flex items-center gap-3 rounded-lg bg-gray-800/50 p-3 text-left transition-colors hover:bg-gray-800">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400"><Target size={18} /></div>
              <div><div className="text-sm font-medium">Generate Opportunities</div><div className="text-xs text-gray-500">See what to post about</div></div>
            </button>
            <button onClick={() => navigate('/settings')} className="flex items-center gap-3 rounded-lg bg-gray-800/50 p-3 text-left transition-colors hover:bg-gray-800">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10 text-green-400"><Sparkles size={18} /></div>
              <div><div className="text-sm font-medium">Add AI API Key</div><div className="text-xs text-gray-500">Unlock AI-powered features</div></div>
            </button>
          </div>
        </div>
      )}

      {hasData && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Memories', value: stats?.total_memories || 0, icon: Brain, color: 'text-blue-400' },
            { label: 'Events', value: stats?.total_events || 0, icon: TrendingUp, color: 'text-green-400' },
            { label: 'Opportunities', value: stats?.pending_opportunities || 0, icon: Target, color: 'text-amber-400' },
            { label: 'Journal Entries', value: stats?.journal_entries || 0, icon: BookOpen, color: 'text-purple-400' },
          ].map(s => (
            <div key={s.label} className="card flex items-center gap-4">
              <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gray-800 ${s.color}`}>
                <s.icon size={22} />
              </div>
              <div>
                <div className="text-2xl font-bold">{s.value}</div>
                <div className="text-sm text-gray-500">{s.label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {briefing && (
        <div className="card">
          <div className="mb-4 flex items-center gap-2">
            <Sparkles size={20} className="text-brand-400" />
            <h2 className="text-lg font-semibold">Today's Briefing</h2>
          </div>
          <div className="prose prose-invert max-w-none text-sm leading-relaxed text-gray-300 whitespace-pre-wrap">
            {briefing.text || briefing.briefing || 'No briefing available yet.'}
          </div>
        </div>
      )}

      {recentEntries.length > 0 && (
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen size={20} className="text-purple-400" />
              <h2 className="text-lg font-semibold">Recent Journal Entries</h2>
            </div>
            <button onClick={() => navigate('/journal')} className="text-xs text-brand-400 hover:text-brand-300">View all</button>
          </div>
          <div className="space-y-2">
            {recentEntries.map((e: any) => (
              <div key={e.id} className="rounded-lg bg-gray-800/50 p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="badge bg-gray-800 text-gray-400 text-xs">{e.entry_type}</span>
                  <span className="text-xs text-gray-600">{e.created_at ? new Date(e.created_at).toLocaleDateString() : ''}</span>
                </div>
                <p className="text-sm text-gray-300 line-clamp-2">{e.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flame size={20} className="text-orange-400" />
            <h2 className="text-lg font-semibold">Trending in Your Space</h2>
          </div>
          <button onClick={refreshTrends} disabled={scanningTrends} className="btn-secondary text-xs flex items-center gap-1.5">
            {scanningTrends ? <div className="h-3 w-3 animate-spin rounded-full border border-white border-t-transparent" /> : <TrendingUp size={12} />}
            Refresh
          </button>
        </div>
        {trends.length === 0 ? (
          <p className="text-sm text-gray-500">No trends loaded yet. Click Refresh to scan.</p>
        ) : (
          <div className="space-y-3">
            {trends.slice(0, 5).map((t: any, i: number) => (
              <div key={i} className="flex items-start gap-3 rounded-lg bg-gray-800/50 p-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500/10 text-orange-400 text-sm font-bold">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-sm">{t.title || t.topic}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{t.summary || t.why_now}</div>
                </div>
                <span className={`badge text-xs ${t.urgency === 'breaking' ? 'bg-red-500/10 text-red-400' : t.urgency === 'trending' ? 'bg-amber-500/10 text-amber-400' : 'bg-gray-500/10 text-gray-400'}`}>
                  {t.urgency || 'trending'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <button onClick={() => navigate('/opportunities')} className="card group flex items-center justify-between transition-all hover:border-brand-600">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600/10 text-brand-400"><Target size={22} /></div>
            <div className="text-left">
              <div className="font-semibold">View Opportunities</div>
              <div className="text-sm text-gray-500">See what actions are recommended</div>
            </div>
          </div>
          <ArrowRight size={18} className="text-gray-600 group-hover:text-brand-400" />
        </button>
        <button onClick={() => navigate('/journal')} className="card group flex items-center justify-between transition-all hover:border-brand-600">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-600/10 text-purple-400"><BookOpen size={22} /></div>
            <div className="text-left">
              <div className="font-semibold">Add to Journal</div>
              <div className="text-sm text-gray-500">Capture what you worked on today</div>
            </div>
          </div>
          <ArrowRight size={18} className="text-gray-600 group-hover:text-brand-400" />
        </button>
        <button onClick={() => navigate('/scanner')} className="card group flex items-center justify-between transition-all hover:border-brand-600">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-600/10 text-green-400"><Search size={22} /></div>
            <div className="text-left">
              <div className="font-semibold">Scan LinkedIn Posts</div>
              <div className="text-sm text-gray-500">Analyze posts and get comment ideas</div>
            </div>
          </div>
          <ArrowRight size={18} className="text-gray-600 group-hover:text-brand-400" />
        </button>
      </div>
    </div>
  )
}
