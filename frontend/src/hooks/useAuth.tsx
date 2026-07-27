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
  loginWithTokens: (access: string, refresh: string) => void
  register: (email: string, name: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (api.hasToken()) {
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

  const loginWithTokens = useCallback((access: string, refresh: string) => {
    api.setTokens(access, refresh)
    api.get('/auth/me').then(u => setUser(u)).catch(() => {})
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
    <AuthContext.Provider value={{ user, loading, login, loginWithTokens, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
