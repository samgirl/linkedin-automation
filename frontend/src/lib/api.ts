// API client — works in both dev (proxy) and prod (direct backend URL)
const API_BASE = import.meta.env.VITE_API_URL || '/api'

class ApiClient {
  private accessToken: string | null = null
  private refreshToken: string | null = null

  constructor() {
    this.accessToken = localStorage.getItem('access_token')
    this.refreshToken = localStorage.getItem('refresh_token')
  }

  setTokens(access: string, refresh: string) {
    this.accessToken = access
    this.refreshToken = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  clearTokens() {
    this.accessToken = null
    this.refreshToken = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  private async request<T = any>(method: string, path: string, body?: any): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (this.accessToken) headers['Authorization'] = `Bearer ${this.accessToken}`

    let resp = await fetch(`${API_BASE}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined })

    if (resp.status === 401 && this.refreshToken) {
      const refreshResp = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      })
      if (refreshResp.ok) {
        const data = await refreshResp.json()
        this.setTokens(data.access_token, data.refresh_token)
        headers['Authorization'] = `Bearer ${data.access_token}`
        resp = await fetch(`${API_BASE}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined })
      } else {
        this.clearTokens()
        window.location.href = '/login'
        throw new Error('Session expired')
      }
    }

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(err.detail || 'Request failed')
    }
    return resp.json()
  }

  get<T = any>(path: string) { return this.request<T>('GET', path) }
  post<T = any>(path: string, body?: any) { return this.request<T>('POST', path, body) }
  put<T = any>(path: string, body?: any) { return this.request<T>('PUT', path, body) }
  del<T = any>(path: string) { return this.request<T>('DELETE', path) }
}

export const api = new ApiClient()
