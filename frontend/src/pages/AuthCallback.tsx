import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function AuthCallback() {
  const { loginWithTokens } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    // Parse tokens from hash fragment (more secure than query params)
    const hash = window.location.hash.substring(1)
    const params = new URLSearchParams(hash)
    const access = params.get('access')
    const refresh = params.get('refresh')

    // Fallback: check query params (for backward compatibility)
    const accessQuery = new URLSearchParams(window.location.search).get('access')
    const refreshQuery = new URLSearchParams(window.location.search).get('refresh')

    const finalAccess = access || accessQuery
    const finalRefresh = refresh || refreshQuery

    if (finalAccess && finalRefresh) {
      // Clear the URL hash so tokens aren't visible
      window.history.replaceState({}, '', window.location.pathname)
      loginWithTokens(finalAccess, finalRefresh)
      navigate('/')
    } else {
      navigate('/login?error=OAuth+failed')
    }
  }, [navigate, loginWithTokens])

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
