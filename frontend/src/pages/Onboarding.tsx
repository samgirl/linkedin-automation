import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Briefcase, Building2, Lightbulb, Target, ArrowRight, ArrowLeft, Check } from 'lucide-react'

export default function Onboarding() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [role, setRole] = useState('')
  const [industry, setIndustry] = useState('')
  const [interests, setInterests] = useState('')
  const [goals, setGoals] = useState('')
  const [expertise, setExpertise] = useState('')

  const steps = [
    { title: "What's your role?", desc: "This helps us tailor content suggestions to your position.", icon: Briefcase },
    { title: "What industry?", desc: "We'll find trends and opportunities specific to your space.", icon: Building2 },
    { title: "Your interests", desc: "Topics you care about and want to be known for.", icon: Lightbulb },
    { title: "Your goals", desc: "What do you want to achieve on LinkedIn?", icon: Target },
  ]

  const handleSubmit = async () => {
    setError('')
    setLoading(true)
    try {
      await api.post('/auth/onboarding', {
        role,
        industry,
        interests: interests.split(',').map(s => s.trim()).filter(Boolean),
        goals: goals.split(',').map(s => s.trim()).filter(Boolean),
        expertise,
      })
      navigate('/')
    } catch (e: any) {
      setError(e.message || 'Failed to save. Please try again.')
    }
    setLoading(false)
  }

  const canNext = () => {
    if (step === 0) return role.trim().length > 0
    if (step === 1) return industry.trim().length > 0
    return true
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 p-4">
      <div className="w-full max-w-lg">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-2xl font-bold">P</div>
          <h1 className="text-2xl font-bold">Welcome to PROS</h1>
          <p className="mt-1 text-sm text-gray-500">Let's set up your profile in 30 seconds</p>
        </div>

        <div className="mb-6 flex justify-center gap-2">
          {steps.map((_, i) => (
            <div key={i} className={`h-1.5 w-12 rounded-full transition-colors ${i <= step ? 'bg-brand-500' : 'bg-gray-800'}`} />
          ))}
        </div>

        <div className="card">
          {(() => {
            const Icon = steps[step].icon
            return (
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600/20">
                  <Icon size={20} className="text-brand-400" />
                </div>
                <div>
                  <h2 className="font-semibold">{steps[step].title}</h2>
                  <p className="text-xs text-gray-500">{steps[step].desc}</p>
                </div>
              </div>
            )
          })()}

          {step === 0 && (
            <input className="input" placeholder="e.g. Software Engineer, Marketing Manager, Founder" value={role} onChange={e => setRole(e.target.value)} autoFocus />
          )}
          {step === 1 && (
            <input className="input" placeholder="e.g. SaaS, Healthcare, E-commerce, AI" value={industry} onChange={e => setIndustry(e.target.value)} autoFocus />
          )}
          {step === 2 && (
            <div className="space-y-3">
              <input className="input" placeholder="Interests (comma-separated): AI, startups, leadership" value={interests} onChange={e => setInterests(e.target.value)} autoFocus />
              <input className="input" placeholder="Expertise (comma-separated): Python, growth marketing, product design" value={expertise} onChange={e => setExpertise(e.target.value)} />
            </div>
          )}
          {step === 3 && (
            <input className="input" placeholder="Goals (comma-separated): Build personal brand, find clients, share expertise" value={goals} onChange={e => setGoals(e.target.value)} autoFocus />
          )}

          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

          <div className="mt-6 flex justify-between">
            {step > 0 ? (
              <button onClick={() => setStep(step - 1)} className="btn-secondary flex items-center gap-1">
                <ArrowLeft size={16} /> Back
              </button>
            ) : <div />}
            {step < 3 ? (
              <button onClick={() => setStep(step + 1)} disabled={!canNext()} className="btn-primary flex items-center gap-1">
                Next <ArrowRight size={16} />
              </button>
            ) : (
              <button onClick={handleSubmit} disabled={loading} className="btn-primary flex items-center gap-1">
                {loading ? 'Setting up...' : 'Complete Setup'} <Check size={16} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
