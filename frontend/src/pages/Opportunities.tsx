import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { Target, MessageSquare, Pen, UserPlus, Share2, Check, X, Sparkles, TrendingUp, Search, ExternalLink } from 'lucide-react'

const typeConfig: Record<string, { icon: any; color: string; label: string }> = {
  post_idea: { icon: Pen, color: 'text-blue-400 bg-blue-400/10', label: 'Post Idea' },
  comment_opportunity: { icon: MessageSquare, color: 'text-green-400 bg-green-400/10', label: 'Comment' },
  connect: { icon: UserPlus, color: 'text-purple-400 bg-purple-400/10', label: 'Connect' },
  outreach: { icon: Share2, color: 'text-amber-400 bg-amber-400/10', label: 'Outreach' },
  trend: { icon: TrendingUp, color: 'text-cyan-400 bg-cyan-400/10', label: 'Trend' },
}

export default function Opportunities() {
  const [opps, setOpps] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState<string | null>(null)
  const [draftPreview, setDraftPreview] = useState<any>(null)
  const [postUrl, setPostUrl] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'recommended' | 'scan' | 'analyze'>('recommended')

  useEffect(() => {
    api.get('/opportunities/').then(setOpps).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const dismiss = async (id: string) => {
    try {
      await api.post(`/opportunities/${id}/dismiss`)
      setOpps(opps.filter(o => o.id !== id))
    } catch (e) { console.error(e) }
  }

  const handleDraft = async (id: string) => {
    setGenerating(id)
    try {
      const draft = await api.post(`/opportunities/${id}/draft`)
      setDraftPreview(draft)
    } catch (e) { console.error(e) }
    setGenerating(null)
  }

  const analyzePost = async () => {
    if (!postUrl.trim()) return
    setAnalyzing(true)
    setAnalysisResult(null)
    try {
      const result = await api.post('/scanner/analyze-post', { url: postUrl })
      setAnalysisResult(result)
    } catch (e) { console.error(e) }
    setAnalyzing(false)
  }

  const generateOpps = async () => {
    setLoading(true)
    try {
      const result = await api.post('/scanner/generate-opportunities')
      setOpps(result?.opportunities || [])
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  if (loading) return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" /></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Opportunities</h1>
          <p className="text-gray-500">AI-recommended actions and post scanning</p>
        </div>
        <button onClick={generateOpps} className="btn-primary flex items-center gap-2">
          <Sparkles size={16} /> Generate More
        </button>
      </div>

      <div className="flex gap-2 border-b border-gray-800 pb-2">
        {[
          { key: 'recommended' as const, label: 'Recommended', icon: Target },
          { key: 'scan' as const, label: 'Scan Posts', icon: Search },
          { key: 'analyze' as const, label: 'Analyze URL', icon: ExternalLink },
        ].map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.key ? 'bg-brand-600/10 text-brand-400 border-b-2 border-brand-400' : 'text-gray-500 hover:text-gray-300'
            }`}>
            <tab.icon size={14} /> {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'analyze' && (
        <div className="card">
          <h3 className="mb-3 font-medium text-gray-300">Analyze a LinkedIn Post</h3>
          <p className="mb-3 text-sm text-gray-500">Paste a LinkedIn post URL to get AI-powered insights and a suggested comment.</p>
          <div className="flex gap-2">
            <input className="input flex-1" placeholder="https://www.linkedin.com/posts/..." value={postUrl} onChange={e => setPostUrl(e.target.value)} />
            <button onClick={analyzePost} disabled={analyzing || !postUrl.trim()} className="btn-primary flex items-center gap-2">
              {analyzing ? <div className="h-4 w-4 animate-spin rounded-full border border-white border-t-transparent" /> : <Search size={14} />}
              Analyze
            </button>
          </div>
          {analysisResult && (
            <div className="mt-4 space-y-3">
              <div className="rounded-lg bg-gray-800 p-4">
                <div className="text-xs text-gray-500 mb-1">Post Content</div>
                <div className="text-sm text-gray-300">{analysisResult.post_content}</div>
              </div>
              <div className="rounded-lg bg-brand-600/10 border border-brand-600/30 p-4">
                <div className="text-xs text-brand-400 mb-1 font-medium">Suggested Comment</div>
                <div className="text-sm text-gray-300 whitespace-pre-wrap">{analysisResult.suggested_comment}</div>
                <button onClick={() => navigator.clipboard.writeText(analysisResult.suggested_comment)} className="mt-2 text-xs text-brand-400 hover:text-brand-300">Copy comment</button>
              </div>
              {analysisResult.inspired_post_idea && (
                <div className="rounded-lg bg-purple-600/10 border border-purple-600/30 p-4">
                  <div className="text-xs text-purple-400 mb-1 font-medium">Inspired Post Idea</div>
                  <div className="text-sm text-gray-300 whitespace-pre-wrap">{analysisResult.inspired_post_idea}</div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'scan' && (
        <div className="card">
          <h3 className="mb-3 font-medium text-gray-300">Scan for Engagement Opportunities</h3>
          <p className="mb-3 text-sm text-gray-500">AI scans for posts in your space where you can add value.</p>
          <button onClick={async () => {
            setLoading(true)
            try {
              const result = await api.post('/scanner/scan-opportunities')
              setOpps(result?.opportunities || [])
            } catch (e) { console.error(e) }
            setLoading(false)
          }} className="btn-primary flex items-center gap-2">
            <Search size={14} /> Scan Now
          </button>
        </div>
      )}

      {draftPreview && (
        <div className="card border-brand-600">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-semibold">Generated Draft</h3>
            <button onClick={() => setDraftPreview(null)} className="text-gray-500 hover:text-gray-300"><X size={16} /></button>
          </div>
          <div className="whitespace-pre-wrap rounded-lg bg-gray-800 p-4 text-sm text-gray-300">{draftPreview.content}</div>
          <div className="mt-3 flex gap-2">
            <button onClick={() => { navigator.clipboard.writeText(draftPreview.content) }} className="btn-secondary text-xs">Copy</button>
            <button className="btn-primary text-xs">Publish to LinkedIn</button>
          </div>
        </div>
      )}

      {activeTab === 'recommended' && (
        opps.length === 0 ? (
          <div className="card text-center text-gray-500 py-12">
            <Target size={48} className="mx-auto mb-4 text-gray-700" />
            <p>No opportunities yet. Connect your accounts and add context to get recommendations.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {opps.map((o: any, i: number) => {
              const conf = typeConfig[o.type] || typeConfig.post_idea
              const Icon = conf.icon
              return (
                <div key={o.id || i} className="card">
                  <div className="flex items-start gap-4">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${conf.color}`}>
                      <Icon size={18} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{o.title || o.topic}</span>
                        <span className="badge bg-gray-800 text-gray-500">{conf.label}</span>
                        {o.priority && (
                          <span className={`badge text-xs ${o.priority === 'high' ? 'bg-red-500/10 text-red-400' : o.priority === 'medium' ? 'bg-amber-500/10 text-amber-400' : 'bg-gray-500/10 text-gray-400'}`}>
                            {o.priority}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-gray-400">{o.description || o.summary}</p>
                      {o.suggested_action && (
                        <p className="mt-2 text-xs text-brand-400">Action: {o.suggested_action}</p>
                      )}
                      {o.post_hook && (
                        <div className="mt-2 rounded bg-gray-800/50 p-2 text-xs text-gray-400">
                          Hook: "{o.post_hook}"
                        </div>
                      )}
                      {o.talking_points?.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {o.talking_points.map((tp: string, j: number) => (
                            <div key={j} className="text-xs text-gray-500">• {tp}</div>
                          ))}
                        </div>
                      )}
                    </div>
                    {o.id && (
                      <div className="flex flex-col gap-2">
                        <button onClick={() => handleDraft(o.id)} disabled={generating === o.id} className="btn-primary text-xs flex items-center gap-1">
                          {generating === o.id ? <div className="h-3 w-3 animate-spin rounded-full border border-white border-t-transparent" /> : <Sparkles size={12} />}
                          Draft
                        </button>
                        <button onClick={() => dismiss(o.id)} className="btn-secondary text-xs flex items-center gap-1">
                          <X size={12} /> Dismiss
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )
      )}
    </div>
  )
}
