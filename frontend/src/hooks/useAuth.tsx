import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { api } from '../lib/api'

interface User {
  id: string
  email: string
  name: string
  avatar_url?: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, name: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const access = params.get('access')
    const refresh = params.get('refresh')
    if (access && refresh) {
      api.setTokens(access, refresh)
      window.history.replaceState({}, '', window.location.pathname)
    }

    if (api['accessToken']) {
      api.get('/auth/me')
        .then(u => setUser(u))
        .catch(() => { api.clearTokens() })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const resp = await api.post('/auth/login', { email, password })
    api.setTokens(resp.access_token, resp.refresh_token)
    setUser(resp.user)
  }, [])

  const register = useCallback(async (email: string, name: string, password: string) => {
    const resp = await api.post('/auth/register', { email, name, password })
    api.setTokens(resp.access_token, resp.refresh_token)
    setUser(resp.user)
  }, [])

  const logout = useCallback(() => {
    api.clearTokens()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
