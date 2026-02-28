'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Shield, Menu, X, LogOut, User } from 'lucide-react';
import { useState, useEffect } from 'react';

type UserRole = 'citizen' | 'worker' | 'admin' | null;

const allNavLinks = [
  { href: '/', label: 'Home', roles: ['citizen', 'worker', 'admin', null] },
  { href: '/report', label: 'Report Issue', roles: ['citizen', 'admin'] },
  { href: '/worker', label: 'Worker Dashboard', roles: ['worker', 'admin'] },
  { href: '/dashboard', label: 'Admin Dashboard', roles: ['admin'] },
];

const ROLE_LABELS: Record<string, string> = {
  citizen: 'Citizen',
  worker: 'Worker',
  admin: 'Admin',
};

const ROLE_COLORS: Record<string, string> = {
  citizen: 'bg-blue-50 text-blue-700',
  worker: 'bg-amber-50 text-amber-700',
  admin: 'bg-emerald-50 text-emerald-700',
};

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [role, setRole] = useState<UserRole>(null);
  const [workerId, setWorkerId] = useState('');

  useEffect(() => {
    const storedRole = localStorage.getItem('sanitisense_role') as UserRole;
    const storedWorker = localStorage.getItem('sanitisense_worker_id') || '';
    setRole(storedRole);
    setWorkerId(storedWorker);
  }, [pathname]); // re-check on route change

  // Don't show navbar on login page
  if (pathname === '/login') return null;

  const visibleLinks = allNavLinks.filter((link) =>
    link.roles.includes(role || null)
  );

  const handleLogout = () => {
    localStorage.removeItem('sanitisense_role');
    localStorage.removeItem('sanitisense_worker_id');
    setRole(null);
    setWorkerId('');
    router.push('/login');
  };

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <Shield className="h-8 w-8 text-emerald-600" />
            <Link href="/" className="text-xl font-bold text-gray-900">
              Saniti<span className="text-emerald-600">Sense</span>{' '}
              <span className="text-xs font-normal text-amber-500 bg-amber-50 px-1.5 py-0.5 rounded">AI</span>
            </Link>
          </div>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {visibleLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname === link.href
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                {link.label}
              </Link>
            ))}

            {/* Role badge + logout */}
            {role && (
              <div className="flex items-center gap-2 ml-3 pl-3 border-l border-gray-200">
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${ROLE_COLORS[role] || ''}`}>
                  <User className="h-3 w-3 inline mr-1" />
                  {ROLE_LABELS[role]}{workerId ? ` (${workerId})` : ''}
                </span>
                <button
                  onClick={handleLogout}
                  className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  title="Switch role"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            )}
            {!role && (
              <Link
                href="/login"
                className="ml-3 px-3 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors"
              >
                Login
              </Link>
            )}
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden flex items-center"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* Mobile nav */}
      {mobileOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white px-4 py-2">
          {visibleLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileOpen(false)}
              className={`block px-3 py-2 rounded-lg text-sm font-medium ${
                pathname === link.href
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {link.label}
            </Link>
          ))}
          {role ? (
            <button
              onClick={() => { setMobileOpen(false); handleLogout(); }}
              className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 mt-1"
            >
              <LogOut className="h-4 w-4 inline mr-1" /> Switch Role
            </button>
          ) : (
            <Link
              href="/login"
              onClick={() => setMobileOpen(false)}
              className="block px-3 py-2 rounded-lg text-sm font-medium text-emerald-700 bg-emerald-50 mt-1"
            >
              Login
            </Link>
          )}
        </div>
      )}
    </nav>
  );
}
