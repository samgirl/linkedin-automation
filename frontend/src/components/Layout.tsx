import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  LayoutDashboard, Brain, Target, BookOpen, FileText, Plug, Settings, LogOut, Search
} from 'lucide-react'

const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/context', icon: Brain, label: 'Context' },
  { to: '/opportunities', icon: Target, label: 'Opportunities' },
  { to: '/scanner', icon: Search, label: 'Scanner' },
  { to: '/journal', icon: BookOpen, label: 'Journal' },
  { to: '/drafts', icon: FileText, label: 'Drafts' },
  { to: '/connectors', icon: Plug, label: 'Connectors' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="flex h-screen">
      <aside className="flex w-64 flex-col border-r border-gray-800 bg-gray-900">
        <div className="flex items-center gap-3 px-6 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold">P</div>
          <div>
            <div className="text-sm font-semibold">PROS</div>
            <div className="text-xs text-gray-500">Reputation OS</div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3">
          {nav.map(n => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  isActive
                    ? 'bg-brand-600/10 text-brand-400'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                }`
              }
            >
              <n.icon size={18} />
              {n.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-gray-800 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-700 text-xs font-medium">
              {user?.name?.[0] || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{user?.name}</div>
              <div className="text-xs text-gray-500 truncate">{user?.email}</div>
            </div>
            <button onClick={() => { logout(); navigate('/login') }} className="text-gray-500 hover:text-gray-300">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-gray-950 p-8">
        <Outlet />
      </main>
    </div>
  )
}
