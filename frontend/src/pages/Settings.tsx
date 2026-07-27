import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../lib/api'
import { Settings as SettingsIcon, Key, Trash2, Shield, Clock, Bell } from 'lucide-react'

export default function Settings() {
  const { user } = useAuth()
  const [openaiKey, setOpenaiKey] = useState('')
  const [anthropicKey, setAnthropicKey] = useState('')
  const [dailyLimit, setDailyLimit] = useState(30)
  const [alertEnabled, setAlertEnabled] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('prosFocusSettings') || '{}')
      if (saved.dailyLimitMinutes) setDailyLimit(saved.dailyLimitMinutes)
      if (saved.alertEnabled !== undefined) setAlertEnabled(saved.alertEnabled)
    } catch {}
  }, [])

  const saveKeys = async () => {
    setSaving(true)
    try {
      if (openaiKey) await api.post('/connectors/chatgpt/connect', { api_key: openaiKey })
      if (anthropicKey) await api.post('/connectors/claude/connect', { api_key: anthropicKey })
      setMessage('API keys saved!')
      setOpenaiKey('')
      setAnthropicKey('')
    } catch (e: any) { setMessage('Error: ' + e.message) }
    setSaving(false)
    setTimeout(() => setMessage(''), 3000)
  }

  const saveFocusSettings = async () => {
    setSaving(true)
    try {
      // Save to localStorage (extension reads from chrome.storage)
      localStorage.setItem('prosFocusSettings', JSON.stringify({ dailyLimitMinutes: dailyLimit, alertEnabled }))
      // Also try to send to extension if available
      if (typeof (window as any).chrome !== 'undefined' && (window as any).chrome?.storage?.local) {
        (window as any).chrome.storage.local.set({
          prosSettings: { dailyLimitMinutes: dailyLimit, alertEnabled }
        })
      }
      setMessage('Focus settings saved!')
    } catch (e) { console.error(e) }
    setSaving(false)
    setTimeout(() => setMessage(''), 3000)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-500">Manage your account, API keys, and focus preferences</p>
      </div>

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

      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Key size={20} className="text-brand-400" />
          <h2 className="font-semibold">API Keys</h2>
        </div>
        <p className="mb-4 text-sm text-gray-500">Your keys are encrypted at rest. They are used to pull context from your AI conversations.</p>
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">OpenAI API Key (for ChatGPT context)</label>
            <input className="input" type="password" placeholder="sk-..." value={openaiKey} onChange={e => setOpenaiKey(e.target.value)} />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">Anthropic API Key (for Claude context)</label>
            <input className="input" type="password" placeholder="sk-ant-..." value={anthropicKey} onChange={e => setAnthropicKey(e.target.value)} />
          </div>
          <button onClick={saveKeys} disabled={saving} className="btn-primary">
            {saving ? 'Saving...' : 'Save Keys'}
          </button>
          {message && <p className={`text-sm ${message.startsWith('Error') ? 'text-red-400' : 'text-green-400'}`}>{message}</p>}
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
