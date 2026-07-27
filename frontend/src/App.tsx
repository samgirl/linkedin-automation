import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import Layout from './components/Layout'
import Login from './pages/Login'
import AuthCallback from './pages/AuthCallback'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Context from './pages/Context'
import Opportunities from './pages/Opportunities'
import Journal from './pages/Journal'
import Connectors from './pages/Connectors'
import Drafts from './pages/Drafts'
import Settings from './pages/Settings'
import Scanner from './pages/Scanner'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" /></div>
  if (!user) return <Navigate to="/login" />
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="context" element={<Context />} />
          <Route path="opportunities" element={<Opportunities />} />
          <Route path="journal" element={<Journal />} />
          <Route path="drafts" element={<Drafts />} />
          <Route path="connectors" element={<Connectors />} />
          <Route path="scanner" element={<Scanner />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </AuthProvider>
  )
}
