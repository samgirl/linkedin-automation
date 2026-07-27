import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../lib/api'
import { Settings as SettingsIcon, Key, Trash2, Shield, Clock, AlertCircle, Check } from 'lucide-react'

export default function Settings() {
  const { user } = useAuth()
  const [openaiKey, setOpenaiKey] = useState('')
  const [anthropicKey, setAnthropicKey] = useState('')
  const [dailyLimit, setDailyLimit] = useState(30)
  const [alertEnabled, setAlertEnabled] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('prosFocusSettings') || '{}')
      if (saved.dailyLimitMinutes) setDailyLimit(saved.dailyLimitMinutes)
      if (saved.alertEnabled !== undefined) setAlertEnabled(saved.alertEnabled)
    } catch {}
  }, [])

  const saveKeys = async () => {
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      if (openaiKey) await api.post('/connectors/chatgpt/connect', { api_key: openaiKey })
      if (anthropicKey) await api.post('/connectors/claude/connect', { api_key: anthropicKey })
      if (openaiKey || anthropicKey) {
        setSuccess('API keys saved! AI features (Scanner, Drafts, Briefings) are now enabled.')
      } else {
        setError('Please enter at least one API key.')
      }
      setOpenaiKey('')
      setAnthropicKey('')
    } catch (e: any) {
      setError('Failed to save keys: ' + (e.message || 'Unknown error'))
    }
    setSaving(false)
  }

  const saveFocusSettings = async () => {
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      localStorage.setItem('prosFocusSettings', JSON.stringify({ dailyLimitMinutes: dailyLimit, alertEnabled }))
      if (typeof (window as any).chrome !== 'undefined' && (window as any).chrome?.storage?.local) {
        (window as any).chrome.storage.local.set({
          prosSettings: { dailyLimitMinutes: dailyLimit, alertEnabled }
        })
      }
      setSuccess('Focus settings saved!')
    } catch (e: any) {
      setError('Failed to save settings: ' + (e.message || 'Unknown error'))
    }
    setSaving(false)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-500">Manage your account, API keys, and focus preferences</p>
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

      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Shield size={20} className="text-brand-400" />
          <h2 className="font-semibold">Account</h2>
        </div>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between"><span className="text-gray-500">Name</span><span>{user?.name}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Email</span><span>{user?.email}</span></div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Key size={20} className="text-brand-400" />
          <h2 className="font-semibold">AI API Keys</h2>
        </div>
        <p className="mb-4 text-sm text-gray-500">Your keys are encrypted at rest. Add at least one to enable AI-powered features (Scanner, Drafts, Briefings, Trends).</p>
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">OpenAI API Key</label>
            <input className="input" type="password" placeholder="sk-..." value={openaiKey} onChange={e => setOpenaiKey(e.target.value)} />
            <p className="mt-1 text-xs text-gray-600">Enables GPT-4 powered features</p>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">Anthropic API Key</label>
            <input className="input" type="password" placeholder="sk-ant-..." value={anthropicKey} onChange={e => setAnthropicKey(e.target.value)} />
            <p className="mt-1 text-xs text-gray-600">Enables Claude-powered features</p>
          </div>
          <button onClick={saveKeys} disabled={saving} className="btn-primary">
            {saving ? 'Saving...' : 'Save Keys'}
          </button>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Clock size={20} className="text-brand-400" />
          <h2 className="font-semibold">Focus Guard</h2>
        </div>
        <p className="mb-4 text-sm text-gray-500">Set your daily LinkedIn time limit. The Chrome extension will alert you when you're approaching it.</p>
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">Daily LinkedIn limit (minutes)</label>
            <div className="flex items-center gap-3">
              <input type="range" min={10} max={120} step={5} value={dailyLimit} onChange={e => setDailyLimit(Number(e.target.value))} className="flex-1" />
              <span className="w-12 text-center font-mono text-lg font-bold text-brand-400">{dailyLimit}</span>
            </div>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={alertEnabled} onChange={e => setAlertEnabled(e.target.checked)} className="rounded border-gray-600 bg-gray-800 text-brand-500" />
            <span className="text-sm text-gray-300">Show alerts when approaching limit</span>
          </label>
          <button onClick={saveFocusSettings} disabled={saving} className="btn-primary">Save Focus Settings</button>
        </div>
      </div>

      <div className="card border-red-800/50">
        <div className="flex items-center gap-3 mb-4">
          <Trash2 size={20} className="text-red-400" />
          <h2 className="font-semibold text-red-400">Danger Zone</h2>
        </div>
        <p className="mb-4 text-sm text-gray-500">Permanently delete your account and all data.</p>
        <button className="btn-danger text-xs" onClick={() => alert('Contact support to delete your account.')}>Delete Account</button>
      </div>
    </div>
  )
}
