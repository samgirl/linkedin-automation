import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { FileText, Copy, Check, Send, Sparkles, Pen, MessageSquare, UserPlus, Edit3, AlertCircle } from 'lucide-react'

export default function Drafts() {
  const [drafts, setDrafts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [topic, setTopic] = useState('')
  const [type, setType] = useState('post')
  const [copied, setCopied] = useState<string | null>(null)
  const [editing, setEditing] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/drafts/').then(setDrafts).catch((e) => setError('Failed to load drafts: ' + e.message)).finally(() => setLoading(false))
  }, [])

  const generate = async () => {
    if (!topic.trim()) return
    setGenerating(true)
    setError('')
    try {
      const draft = await api.post('/opportunities/generate', { type, topic })
      setDrafts([draft, ...drafts])
      setTopic('')
    } catch (e: any) {
      const msg = e.message || ''
      if (msg.includes('API key')) {
        setError('AI features require an API key. Go to Settings → API Keys to add your OpenAI or Anthropic key.')
      } else {
        setError('Failed to generate draft: ' + msg)
      }
    }
    setGenerating(false)
  }

  const copyDraft = (id: string, content: string) => {
    navigator.clipboard.writeText(content)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  const saveEdit = async (id: string) => {
    try {
      await api.put(`/drafts/${id}`, { content: editContent })
      setDrafts(drafts.map(d => d.id === id ? { ...d, content: editContent } : d))
      setEditing(null)
    } catch (e: any) {
      setError('Failed to save edit: ' + (e.message || 'Unknown error'))
    }
  }

  const publishDraft = async (id: string, content: string) => {
    try {
      await api.post(`/drafts/${id}/publish`)
      setDrafts(drafts.map(d => d.id === id ? { ...d, status: 'published' } : d))
      navigator.clipboard.writeText(content)
      alert('Draft marked as published and copied to clipboard. Paste it into LinkedIn to post.')
    } catch (e: any) {
      setError('Failed to publish: ' + (e.message || 'Unknown error'))
    }
  }

  const typeIcons: Record<string, any> = { post: Pen, comment: MessageSquare, message: UserPlus }

  if (loading) return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" /></div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Drafts</h1>
        <p className="text-gray-500">Generate and manage your LinkedIn content</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
          <AlertCircle size={16} className="flex-shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError('')} className="text-red-400 hover:text-red-300">&times;</button>
        </div>
      )}

      <div className="card">
        <h3 className="mb-3 font-medium text-gray-300">Generate New Draft</h3>
        <div className="flex gap-3">
          <div className="flex gap-1.5">
            {['post', 'comment', 'message'].map(t => (
              <button key={t} onClick={() => setType(t)}
                className={`rounded-lg px-3 py-2 text-xs font-medium transition-colors ${type === t ? 'bg-brand-600/10 text-brand-400' : 'text-gray-500 hover:text-gray-300'}`}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
          <input className="input flex-1" placeholder="Topic or context for the draft..." value={topic} onChange={e => setTopic(e.target.value)} onKeyDown={e => e.key === 'Enter' && generate()} />
          <button onClick={generate} disabled={generating || !topic.trim()} className="btn-primary flex items-center gap-2">
            {generating ? <div className="h-4 w-4 animate-spin rounded-full border border-white border-t-transparent" /> : <Sparkles size={14} />}
            Generate
          </button>
        </div>
        <p className="mt-2 text-xs text-gray-600">Requires an AI API key. Add one in Settings.</p>
      </div>

      <div className="space-y-4">
        {drafts.length === 0 ? (
          <div className="card text-center text-gray-500 py-12">
            <FileText size={48} className="mx-auto mb-4 text-gray-700" />
            <p>No drafts yet. Generate your first one above.</p>
          </div>
        ) : drafts.map(d => {
          const Icon = typeIcons[d.type] || Pen
          return (
            <div key={d.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Icon size={14} className="text-gray-500" />
                  <span className="text-sm font-medium">{d.title || d.type}</span>
                  <span className={`badge ${d.status === 'published' ? 'bg-green-500/10 text-green-400' : d.status === 'approved' ? 'bg-blue-500/10 text-blue-400' : 'bg-gray-500/10 text-gray-400'}`}>
                    {d.status}
                  </span>
                </div>
                <div className="text-xs text-gray-600">{d.created_at ? new Date(d.created_at).toLocaleDateString() : ''}</div>
              </div>

              {editing === d.id ? (
                <div>
                  <textarea className="input min-h-[150px]" value={editContent} onChange={e => setEditContent(e.target.value)} />
                  <div className="mt-2 flex gap-2">
                    <button onClick={() => saveEdit(d.id)} className="btn-primary text-xs">Save</button>
                    <button onClick={() => setEditing(null)} className="btn-secondary text-xs">Cancel</button>
                  </div>
                </div>
              ) : (
                <div className="whitespace-pre-wrap rounded-lg bg-gray-800/50 p-4 text-sm text-gray-300">{d.content}</div>
              )}

              <div className="mt-3 flex gap-2">
                <button onClick={() => copyDraft(d.id, d.content)} className="btn-secondary text-xs flex items-center gap-1">
                  {copied === d.id ? <Check size={12} /> : <Copy size={12} />}
                  {copied === d.id ? 'Copied!' : 'Copy'}
                </button>
                <button onClick={() => { setEditing(d.id); setEditContent(d.content) }} className="btn-secondary text-xs flex items-center gap-1">
                  <Edit3 size={12} /> Edit
                </button>
                {d.status !== 'published' && (
                  <button onClick={() => publishDraft(d.id, d.content)} className="btn-primary text-xs flex items-center gap-1">
                    <Send size={12} /> Publish
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
