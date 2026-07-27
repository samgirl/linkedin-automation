import { useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function AuthCallback() {
  const { loginWithTokens } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const access = searchParams.get('access')
    const refresh = searchParams.get('refresh')

    if (access && refresh) {
      loginWithTokens(access, refresh)
      navigate('/')
    } else {
      navigate('/login')
    }
  }, [searchParams, navigate, loginWithTokens])

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950">
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-2xl font-bold">P</div>
        <p className="text-gray-400">Signing you in...</p>
        <div className="mt-4 h-6 w-6 animate-spin rounded-full border-2 border-brand-500 border-t-transparent mx-auto" />
      </div>
    </div>
  )
}
