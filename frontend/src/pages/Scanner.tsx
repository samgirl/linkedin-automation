import { useState } from 'react'
import { api } from '../lib/api'
import { Search, ExternalLink, Copy, Check, Flame, TrendingUp, Newspaper, AlertCircle } from 'lucide-react'

export default function Scanner() {
  const [postUrl, setPostUrl] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<any>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [linkedinTrends, setLinkedinTrends] = useState<any[]>([])
  const [loadingTrends, setLoadingTrends] = useState(false)
  const [newsQuery, setNewsQuery] = useState('')
  const [news, setNews] = useState<any[]>([])
  const [loadingNews, setLoadingNews] = useState(false)
  const [error, setError] = useState('')

  const analyzePost = async () => {
    if (!postUrl.trim()) return
    setAnalyzing(true)
    setAnalysis(null)
    setError('')
    try {
      const result = await api.post('/scanner/analyze-post', { url: postUrl })
      if (result.error) {
        setError(result.error)
      } else {
        setAnalysis(result)
      }
    } catch (e: any) {
      const msg = e.message || ''
      if (msg.includes('API key')) {
        setError('AI features require an API key. Go to Settings → API Keys to add your OpenAI or Anthropic key.')
      } else {
        setError('Failed to analyze post: ' + msg)
      }
    }
    setAnalyzing(false)
  }

  const loadLinkedInTrends = async () => {
    setLoadingTrends(true)
    setError('')
    try {
      const result = await api.get('/scanner/linkedin-trends')
      setLinkedinTrends(result?.trends || [])
      if (!result?.trends?.length) {
        setError('No trends found. Add your expertise to Context first, or add an AI API key in Settings.')
      }
    } catch (e: any) {
      const msg = e.message || ''
      if (msg.includes('API key')) {
        setError('AI features require an API key. Go to Settings → API Keys.')
      } else {
        setError('Failed to load trends: ' + msg)
      }
    }
    setLoadingTrends(false)
  }

  const scanNews = async () => {
    setLoadingNews(true)
    setError('')
    try {
      const result = await api.post('/scanner/scan-news', { query: newsQuery || undefined })
      setNews(result?.articles || [])
      if (!result?.articles?.length) {
        setError('No articles found. Add an AI API key in Settings for news scanning.')
      }
    } catch (e: any) {
      const msg = e.message || ''
      if (msg.includes('API key')) {
        setError('AI features require an API key. Go to Settings → API Keys.')
      } else {
        setError('Failed to scan news: ' + msg)
      }
    }
    setLoadingNews(false)
  }

  const copyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">LinkedIn Scanner</h1>
        <p className="text-gray-500">Analyze posts, find trends, and discover engagement opportunities</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
          <AlertCircle size={16} className="flex-shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError('')} className="text-red-400 hover:text-red-300">&times;</button>
        </div>
      )}

      {/* Post URL Analyzer */}
      <div className="card">
        <div className="mb-4 flex items-center gap-2">
          <Search size={20} className="text-brand-400" />
          <h2 className="text-lg font-semibold">Analyze a LinkedIn Post</h2>
        </div>
        <p className="mb-3 text-sm text-gray-500">Paste any LinkedIn post URL to get AI-powered insights and a suggested comment.</p>
        <div className="flex gap-2">
          <input
            className="input flex-1"
            placeholder="https://www.linkedin.com/posts/..."
            value={postUrl}
            onChange={e => setPostUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && analyzePost()}
          />
          <button onClick={analyzePost} disabled={analyzing || !postUrl.trim()} className="btn-primary flex items-center gap-2">
            {analyzing ? <div className="h-4 w-4 animate-spin rounded-full border border-white border-t-transparent" /> : <Search size={14} />}
            Analyze
          </button>
        </div>

        {analysis && (
          <div className="mt-6 space-y-4">
            <div className="rounded-lg bg-gray-800/50 p-4">
              <div className="text-xs text-gray-500 mb-2 font-medium">POST CONTENT</div>
              <div className="text-sm text-gray-300">{analysis.post_content}</div>
            </div>

            <div className="rounded-lg bg-brand-600/10 border border-brand-600/30 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs text-brand-400 font-medium">SUGGESTED COMMENT</div>
                <button onClick={() => copyText(analysis.suggested_comment, 'comment')} className="flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300">
                  {copied === 'comment' ? <Check size={12} /> : <Copy size={12} />}
                  {copied === 'comment' ? 'Copied' : 'Copy'}
                </button>
              </div>
              <div className="text-sm text-gray-300 whitespace-pre-wrap">{analysis.suggested_comment}</div>
            </div>

            {analysis.inspired_post_idea && (
              <div className="rounded-lg bg-purple-600/10 border border-purple-600/30 p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-xs text-purple-400 font-medium">INSPIRED POST IDEA</div>
                  <button onClick={() => copyText(analysis.inspired_post_idea, 'idea')} className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300">
                    {copied === 'idea' ? <Check size={12} /> : <Copy size={12} />}
                    {copied === 'idea' ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <div className="text-sm text-gray-300 whitespace-pre-wrap">{analysis.inspired_post_idea}</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* LinkedIn Trends */}
      <div className="card">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flame size={20} className="text-orange-400" />
            <h2 className="text-lg font-semibold">LinkedIn Trends in Your Space</h2>
          </div>
          <button onClick={loadLinkedInTrends} disabled={loadingTrends} className="btn-secondary text-xs flex items-center gap-1.5">
            {loadingTrends ? <div className="h-3 w-3 animate-spin rounded-full border border-white border-t-transparent" /> : <TrendingUp size={12} />}
            Scan Trends
          </button>
        </div>

        {linkedinTrends.length === 0 ? (
          <p className="text-sm text-gray-500">Click "Scan Trends" to find trending topics in your industry. Requires an AI API key.</p>
        ) : (
          <div className="space-y-3">
            {linkedinTrends.map((t: any, i: number) => (
              <div key={i} className="rounded-lg bg-gray-800/50 p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{t.topic}</div>
                    <div className="text-xs text-gray-500 mt-1">{t.why_now}</div>
                    {t.post_hook && (
                      <div className="mt-2 rounded bg-gray-900 p-2 text-xs text-brand-400">
                        Hook: "{t.post_hook}"
                      </div>
                    )}
                    {t.talking_points?.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {t.talking_points.map((tp: string, j: number) => (
                          <div key={j} className="text-xs text-gray-500">• {tp}</div>
                        ))}
                      </div>
                    )}
                  </div>
                  <span className={`badge text-xs ml-3 ${
                    t.competition_level === 'low' ? 'bg-green-500/10 text-green-400'
                    : t.competition_level === 'high' ? 'bg-red-500/10 text-red-400'
                    : 'bg-amber-500/10 text-amber-400'
                  }`}>
                    {t.competition_level || 'medium'} competition
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* News Scanner */}
      <div className="card">
        <div className="mb-4 flex items-center gap-2">
          <Newspaper size={20} className="text-cyan-400" />
          <h2 className="text-lg font-semibold">News Scanner</h2>
        </div>
        <p className="mb-3 text-sm text-gray-500">Scan for news articles relevant to your industry.</p>
        <div className="flex gap-2">
          <input
            className="input flex-1"
            placeholder="Enter a topic or leave blank for your defaults..."
            value={newsQuery}
            onChange={e => setNewsQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && scanNews()}
          />
          <button onClick={scanNews} disabled={loadingNews} className="btn-primary flex items-center gap-2">
            {loadingNews ? <div className="h-4 w-4 animate-spin rounded-full border border-white border-t-transparent" /> : <Newspaper size={14} />}
            Scan
          </button>
        </div>

        {news.length > 0 && (
          <div className="mt-4 space-y-3">
            {news.map((a: any, i: number) => (
              <div key={i} className="rounded-lg bg-gray-800/50 p-3">
                <div className="font-medium text-sm">{a.headline}</div>
                <div className="text-xs text-gray-500 mt-1">{a.source} — {a.summary}</div>
                {a.angle && (
                  <div className="mt-2 text-xs text-brand-400">Your angle: {a.angle}</div>
                )}
                {a.url && (
                  <a href={a.url} target="_blank" rel="noopener" className="mt-1 inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300">
                    <ExternalLink size={10} /> Read article
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
