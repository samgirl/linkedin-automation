import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, Brain, Users, MessageSquare, Settings } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/memory', label: 'Memory', icon: Brain },
  { path: '/identity', label: 'Identity', icon: Users },
  { path: '/reflection', label: 'Reflect', icon: MessageSquare },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export function Layout() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-[#141414] border-r border-[#2a2a2a] flex flex-col">
        <div className="p-6 border-b border-[#2a2a2a]">
          <h1 className="text-xl font-bold">PROS</h1>
          <p className="text-xs text-[#666] mt-1">AI Coworker</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-[#3b82f6] text-white'
                    : 'text-[#a0a0a0] hover:bg-[#1f1f1f] hover:text-white'
                }`
              }
            >
              <item.icon size={18} />
              <span className="text-sm">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        
        <div className="p-4 border-t border-[#2a2a2a]">
          <div className="text-xs text-[#666]">
            <p>Status: <span className="text-[#10b981]">Active</span></p>
          </div>
        </div>
      </aside>
      
      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
