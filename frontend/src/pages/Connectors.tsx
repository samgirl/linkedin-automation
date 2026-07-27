import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { Plug, MessageSquare, Brain, RefreshCw, Trash2, Key, Upload, ExternalLink, AlertCircle, Check } from 'lucide-react'

const providerConfig: Record<string, { icon: any; color: string; label: string; description: string }> = {
  linkedin: { icon: () => <span className="text-lg font-bold">in</span>, color: 'text-blue-400 bg-blue-400/10', label: 'LinkedIn', description: 'Sync your profile, posts, and activity' },
  chatgpt: { icon: MessageSquare, color: 'text-green-400 bg-green-400/10', label: 'ChatGPT', description: 'Import conversations via API key or file upload' },
  claude: { icon: Brain, color: 'text-purple-400 bg-purple-400/10', label: 'Claude', description: 'Import conversations via API key or file upload' },
  google: { icon: () => <span className="text-lg">G</span>, color: 'text-amber-400 bg-amber-400/10', label: 'Google', description: 'Calendar events and Gmail metadata' },
}

export default function Connectors() {
  const [connections, setConnections] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [apiKey, setApiKey] = useState('')
  const [connectingProvider, setConnectingProvider] = useState<string | null>(null)
  const [syncing, setSyncing] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    api.get('/connectors/').then(setConnections).catch((e) => setError('Failed to load connectors: ' + e.message)).finally(() => setLoading(false))
  }, [])

  const connectLinkedIn = async () => {
    setError('')
    setSuccess('')
    try {
      const resp = await api.get('/auth/linkedin')
      window.location.href = resp.url
    } catch (e: any) {
      setError(e.message || 'LinkedIn is not configured. Add LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET to the server.')
    }
  }

  const connectGoogle = async () => {
    setError('')
    setSuccess('')
    try {
      const resp = await api.get('/auth/google')
      window.location.href = resp.url
    } catch (e: any) {
      setError(e.message || 'Google is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to the server.')
    }
  }

  const connectWithApiKey = async (provider: string) => {
    if (!apiKey.trim()) return
    setConnectingProvider(provider)
    setError('')
    setSuccess('')
    try {
      await api.post(`/connectors/${provider}/connect`, { api_key: apiKey })
      const updated = await api.get('/connectors/')
      setConnections(updated)
      setApiKey('')
      setSuccess(`${provider === 'chatgpt' ? 'ChatGPT' : 'Claude'} API key saved. This key can be used for AI features in Scanner and Drafts.`)
    } catch (e: any) {
      setError(`Failed to save ${provider} API key: ` + (e.message || 'Unknown error'))
    }
    setConnectingProvider(null)
  }

  const handleFileImport = async (provider: string) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json,.txt,.csv'
    input.onchange = async (e: any) => {
      const file = e.target.files[0]
      if (!file) return
      setError('')
      setSuccess('')
      const text = await file.text()
      try {
        const result = await api.post('/connectors/import', { provider, data: text, filename: file.name })
        setSuccess(`Import successful! ${result.events_created} conversations imported into your context.`)
        // Refresh stats
        const updated = await api.get('/connectors/')
        setConnections(updated)
      } catch (err: any) {
        setError('Import failed: ' + (err.message || 'Unknown error'))
      }
    }
    input.click()
  }

  const sync = async (connectionId: string) => {
    setSyncing(connectionId)
    setError('')
    setSuccess('')
    try {
      await api.post(`/connectors/${connectionId}/sync`)
      setSuccess('Sync completed. For ChatGPT/Claude, use the JSON import to bring in conversation data.')
    } catch (e: any) {
      setError('Sync failed: ' + (e.message || 'Unknown error'))
    }
    setSyncing(null)
  }

  const disconnect = async (connectionId: string) => {
    if (!confirm('Disconnect this account?')) return
    setError('')
    setSuccess('')
    try {
      await api.del(`/connectors/${connectionId}`)
      setConnections(connections.filter(c => c.id !== connectionId))
      setSuccess('Disconnected successfully.')
    } catch (e: any) {
      setError('Disconnect failed: ' + (e.message || 'Unknown error'))
    }
  }

  if (loading) return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" /></div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Connectors</h1>
        <p className="text-gray-500">Connect your accounts to build context</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
          <AlertCircle size={16} className="flex-shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError('')} className="text-red-400 hover:text-red-300">&times;</button>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-2 rounded-lg bg-green-500/10 border border-green-500/20 p-3 text-sm text-green-400">
          <Check size={16} className="flex-shrink-0" />
          <span className="flex-1">{success}</span>
          <button onClick={() => setSuccess('')} className="text-green-400 hover:text-green-300">&times;</button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {Object.entries(providerConfig).map(([key, conf]) => {
          const conn = connections.find(c => c.provider === key)
          const Icon = conf.icon
          return (
            <div key={key} className="card">
              <div className="flex items-start gap-4">
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${conf.color}`}>
                  <Icon size={22} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{conf.label}</h3>
                    {conn && <span className="badge bg-green-500/10 text-green-400">Connected</span>}
                  </div>
                  <p className="mt-1 text-sm text-gray-500">{conf.description}</p>

                  {conn ? (
                    <div className="mt-3 space-y-2">
                      <div className="flex gap-2">
                        <button onClick={() => sync(conn.id)} disabled={syncing === conn.id} className="btn-secondary text-xs flex items-center gap-1">
                          <RefreshCw size={12} className={syncing === conn.id ? 'animate-spin' : ''} /> Sync
                        </button>
                        <button onClick={() => disconnect(conn.id)} className="btn-danger text-xs flex items-center gap-1">
                          <Trash2 size={12} /> Disconnect
                        </button>
                      </div>
                      {(key === 'chatgpt' || key === 'claude') && (
                        <p className="text-xs text-gray-600">To import conversations, use "Or import JSON export" below.</p>
                      )}
                    </div>
                  ) : (
                    <div className="mt-3 space-y-3">
                      {key === 'linkedin' && (
                        <button onClick={connectLinkedIn} className="btn-primary text-xs flex items-center gap-1">
                          <ExternalLink size={12} /> Connect via LinkedIn OAuth
                        </button>
                      )}
                      {key === 'google' && (
                        <button onClick={connectGoogle} className="btn-primary text-xs flex items-center gap-1">
                          <ExternalLink size={12} /> Connect via Google OAuth
                        </button>
                      )}
                      {(key === 'chatgpt' || key === 'claude') && (
                        <div>
                          <div className="flex gap-2">
                            <div className="relative flex-1">
                              <Key size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                              <input className="input pl-9 text-xs" placeholder={`${conf.label} API key`} type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} />
                            </div>
                            <button onClick={() => connectWithApiKey(key)} disabled={connectingProvider === key || !apiKey.trim()} className="btn-primary text-xs">
                              {connectingProvider === key ? 'Connecting...' : 'Connect'}
                            </button>
                          </div>
                          <p className="mt-1 text-xs text-gray-600">This key is used for AI features (trends, drafts, briefings).</p>
                          <div className="mt-2">
                            <button onClick={() => handleFileImport(key)} className="btn-secondary text-xs flex items-center gap-1">
                              <Upload size={12} /> Or import JSON export
                            </button>
                            <p className="mt-1 text-xs text-gray-600">Export your {conf.label} data and upload the JSON file to import conversations into your context.</p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
