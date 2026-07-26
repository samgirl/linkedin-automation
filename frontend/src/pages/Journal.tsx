import { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'
import { BookOpen, Plus, Link as LinkIcon, FileText, Mic, MicOff, Send, Users, Clock, Lightbulb } from 'lucide-react'

const entryTypes = [
  { type: 'text', icon: FileText, label: 'Text' },
  { type: 'voice', icon: Mic, label: 'Voice' },
  { type: 'meeting_note', icon: Users, label: 'Meeting' },
  { type: 'idea', icon: Lightbulb, label: 'Idea' },
]

export default function Journal() {
  const [entries, setEntries] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [content, setContent] = useState('')
  const [entryType, setEntryType] = useState('text')
  const [url, setUrl] = useState('')
  const [meetingTitle, setMeetingTitle] = useState('')
  const [meetingParticipants, setMeetingParticipants] = useState('')
  const [meetingDuration, setMeetingDuration] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [recordingTime, setRecordingTime] = useState(0)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const timerRef = useRef<any>(null)

  useEffect(() => {
    Promise.all([
      api.get('/journal/').catch(() => []),
      api.get('/journal/stats').catch(() => null),
    ]).then(([e, s]) => {
      setEntries(e || [])
      setStats(s)
    }).finally(() => setLoading(false))
  }, [])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioBlob(blob)
        stream.getTracks().forEach(t => t.stop())
      }

      recorder.start()
      setIsRecording(true)
      setRecordingTime(0)
      timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000)
    } catch (e) {
      console.error('Microphone access denied:', e)
      alert('Please allow microphone access for voice journal entries.')
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
    clearInterval(timerRef.current)
  }

  const submitVoice = async () => {
    if (!audioBlob) return
    setSubmitting(true)
    try {
      const reader = new FileReader()
      reader.onloadend = async () => {
        const base64 = (reader.result as string).split(',')[1]
        const entry = await api.post('/journal/', {
          content: content || `Voice entry (${recordingTime}s)`,
          entry_type: 'voice',
          audio_data: base64,
          tags: ['voice'],
        })
        setEntries([entry, ...entries])
        setContent('')
        setAudioBlob(null)
        setSubmitting(false)
      }
      reader.readAsDataURL(audioBlob)
    } catch (e) { console.error(e); setSubmitting(false) }
  }

  const submitText = async () => {
    if (!content.trim()) return
    setSubmitting(true)
    try {
      const payload: any = {
        content,
        entry_type: entryType,
      }
      if (entryType === 'meeting_note') {
        payload.title = meetingTitle || 'Untitled Meeting'
        payload.participants = meetingParticipants.split(',').map(s => s.trim()).filter(Boolean)
        payload.duration_minutes = meetingDuration ? parseInt(meetingDuration) : null
      }
      if (entryType === 'link') {
        payload.source_url = url
      }
      const entry = await api.post('/journal/', payload)
      setEntries([entry, ...entries])
      setContent('')
      setUrl('')
      setMeetingTitle('')
      setMeetingParticipants('')
      setMeetingDuration('')
    } catch (e) { console.error(e) }
    setSubmitting(false)
  }

  const addLink = async () => {
    if (!url.trim()) return
    setSubmitting(true)
    try {
      const item = await api.post('/journal/content', { url, title: url })
      setEntries([{ ...item, content: url, entry_type: 'saved_link', created_at: item.created_at }, ...entries])
      setUrl('')
    } catch (e) { console.error(e) }
    setSubmitting(false)
  }

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  if (loading) return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" /></div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Journal</h1>
        <p className="text-gray-500">Capture your daily context — what you worked on, learned, found interesting</p>
      </div>

      {stats && (
        <div className="flex items-center gap-4">
          <div className="badge bg-green-500/10 text-green-400">
            <Clock size={12} /> {stats.streak_days} day streak
          </div>
          <div className="badge bg-gray-500/10 text-gray-400">
            {stats.total} total entries
          </div>
        </div>
      )}

      <div className="card">
        <div className="flex gap-2 mb-4">
          {entryTypes.map(t => (
            <button key={t.type} onClick={() => { setEntryType(t.type); setAudioBlob(null) }}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${entryType === t.type ? 'bg-brand-600/10 text-brand-400' : 'text-gray-500 hover:text-gray-300'}`}>
              <t.icon size={14} /> {t.label}
            </button>
          ))}
        </div>

        {entryType === 'voice' ? (
          <div className="space-y-4">
            {!audioBlob ? (
              <div className="flex flex-col items-center gap-4 py-8">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`h-20 w-20 rounded-full flex items-center justify-center transition-all ${
                    isRecording
                      ? 'bg-red-500/20 text-red-400 animate-pulse ring-4 ring-red-500/30'
                      : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
                  }`}
                >
                  {isRecording ? <MicOff size={32} /> : <Mic size={32} />}
                </button>
                <div className="text-center">
                  {isRecording ? (
                    <div>
                      <div className="text-2xl font-mono text-red-400">{formatTime(recordingTime)}</div>
                      <div className="text-xs text-gray-500">Click to stop recording</div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500">Click to start voice recording</div>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="rounded-lg bg-gray-800 p-3 text-sm text-gray-300">
                  Voice recorded ({formatTime(recordingTime)})
                </div>
                <textarea
                  className="input min-h-[80px] resize-y"
                  placeholder="Add a note to go with this voice entry (optional)"
                  value={content}
                  onChange={e => setContent(e.target.value)}
                />
                <div className="flex gap-2">
                  <button onClick={() => setAudioBlob(null)} className="btn-secondary text-xs">Re-record</button>
                  <button onClick={submitVoice} disabled={submitting} className="btn-primary text-xs flex items-center gap-1.5">
                    {submitting ? <div className="h-3 w-3 animate-spin rounded-full border border-white border-t-transparent" /> : <Send size={12} />}
                    Save Voice Entry
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {entryType === 'meeting_note' && (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <input className="input" placeholder="Meeting title" value={meetingTitle} onChange={e => setMeetingTitle(e.target.value)} />
                <input className="input" placeholder="Participants (comma separated)" value={meetingParticipants} onChange={e => setMeetingParticipants(e.target.value)} />
                <input className="input" placeholder="Duration (min)" type="number" value={meetingDuration} onChange={e => setMeetingDuration(e.target.value)} />
              </div>
            )}
            <textarea
              className="input min-h-[120px] resize-y"
              placeholder={
                entryType === 'meeting_note' ? 'Paste meeting notes or transcript...'
                : entryType === 'idea' ? 'What idea do you want to capture?'
                : entryType === 'link' ? 'Add notes about this link...'
                : 'What did you work on today? What did you learn?'
              }
              value={content}
              onChange={e => setContent(e.target.value)}
            />
            {entryType === 'link' && (
              <input className="input" placeholder="https://..." value={url} onChange={e => setUrl(e.target.value)} />
            )}
          </div>
        )}

        {entryType !== 'voice' && (
          <div className="mt-3 flex justify-end">
            <button onClick={submitText} disabled={submitting || !content.trim()} className="btn-primary flex items-center gap-2">
              {submitting ? <div className="h-4 w-4 animate-spin rounded-full border border-white border-t-transparent" /> : <Send size={14} />}
              Add Entry
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <h3 className="mb-3 font-medium text-gray-300">Quick Link Drop</h3>
        <div className="flex gap-2">
          <input className="input flex-1" placeholder="Paste a link you found interesting..." value={url} onChange={e => setUrl(e.target.value)} onKeyDown={e => e.key === 'Enter' && addLink()} />
          <button onClick={addLink} disabled={submitting || !url.trim()} className="btn-secondary flex items-center gap-2">
            <LinkIcon size={14} /> Save
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="font-medium text-gray-300">Recent Entries</h3>
        {entries.length === 0 ? (
          <div className="card text-center text-gray-500 py-8">
            <BookOpen size={40} className="mx-auto mb-3 text-gray-700" />
            <p>No entries yet. Start journaling to build your context.</p>
          </div>
        ) : entries.map(e => (
          <div key={e.id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`badge ${
                    e.entry_type === 'meeting_note' ? 'bg-amber-500/10 text-amber-400'
                    : e.entry_type === 'voice' ? 'bg-pink-500/10 text-pink-400'
                    : e.entry_type === 'idea' ? 'bg-yellow-500/10 text-yellow-400'
                    : e.entry_type === 'link' || e.entry_type === 'saved_link' ? 'bg-blue-500/10 text-blue-400'
                    : 'bg-gray-500/10 text-gray-400'
                  }`}>
                    {e.entry_type === 'meeting_note' ? 'Meeting'
                    : e.entry_type === 'voice' ? 'Voice'
                    : e.entry_type === 'idea' ? 'Idea'
                    : e.entry_type === 'link' || e.entry_type === 'saved_link' ? 'Link'
                    : 'Journal'}
                  </span>
                </div>
                <p className="text-sm text-gray-300 whitespace-pre-wrap line-clamp-4">{e.content}</p>
                {e.source_url && (
                  <a href={e.source_url} target="_blank" rel="noopener" className="mt-1 inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300">
                    <LinkIcon size={10} /> {e.source_url}
                  </a>
                )}
              </div>
              <div className="text-xs text-gray-600 ml-4">
                {e.created_at ? new Date(e.created_at).toLocaleDateString() : ''}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
