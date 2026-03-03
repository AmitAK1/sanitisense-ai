'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Camera, HardHat, BarChart3, Shield, ArrowRight, User, Lock } from 'lucide-react';

export type UserRole = 'citizen' | 'worker' | 'admin';

interface RoleOption {
  role: UserRole;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  borderColor: string;
  redirect: string;
}

const roles: RoleOption[] = [
  {
    role: 'citizen',
    title: 'Citizen',
    description: 'Report sanitation issues with just a photo. Track your complaints.',
    icon: Camera,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 hover:bg-blue-100',
    borderColor: 'border-blue-200 hover:border-blue-400',
    redirect: '/report',
  },
  {
    role: 'worker',
    title: 'Sanitation Worker',
    description: 'View assigned tasks, navigate to locations, upload proof of cleanup.',
    icon: HardHat,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 hover:bg-amber-100',
    borderColor: 'border-amber-200 hover:border-amber-400',
    redirect: '/worker',
  },
  {
    role: 'admin',
    title: 'Municipal Authority',
    description: 'Real-time dashboard, ward heatmap, analytics & AI epidemic advisories.',
    icon: BarChart3,
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50 hover:bg-emerald-100',
    borderColor: 'border-emerald-200 hover:border-emerald-400',
    redirect: '/dashboard',
  },
];

export default function LoginPage() {
  const router = useRouter();
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [workerId, setWorkerId] = useState('W-001');
  const [showWorkerInput, setShowWorkerInput] = useState(false);
  const [showAdminInput, setShowAdminInput] = useState(false);
  const [adminPass, setAdminPass] = useState('');

  const handleRoleSelect = (option: RoleOption) => {
    setSelectedRole(option.role);

    if (option.role === 'worker') {
      setShowWorkerInput(true);
      setShowAdminInput(false);
      return;
    }

    if (option.role === 'admin') {
      setShowAdminInput(true);
      setShowWorkerInput(false);
      return;
    }

    // Citizen — save role and redirect immediately
    localStorage.setItem('sanitisense_role', option.role);
    localStorage.removeItem('sanitisense_worker_id');
    router.push(option.redirect);
  };

  const handleAdminLogin = () => {
    // Demo: accept any non-empty password
    if (!adminPass.trim()) return;
    localStorage.setItem('sanitisense_role', 'admin');
    localStorage.removeItem('sanitisense_worker_id');
    router.push('/dashboard');
  };

  const handleWorkerLogin = () => {
    if (!workerId.trim()) return;
    localStorage.setItem('sanitisense_role', 'worker');
    localStorage.setItem('sanitisense_worker_id', workerId.trim());
    router.push('/worker');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 flex flex-col">
      {/* Header */}
      <div className="text-center pt-12 pb-6 px-4">
        <div className="flex items-center justify-center gap-2 mb-4">
          <Shield className="h-10 w-10 text-emerald-600" />
          <h1 className="text-3xl font-bold text-gray-900">
            Saniti<span className="text-emerald-600">Sense</span>{' '}
            <span className="text-sm font-normal text-amber-500 bg-amber-50 px-2 py-0.5 rounded">
              AI
            </span>
          </h1>
        </div>
        <p className="text-gray-500 max-w-md mx-auto">
          AI-powered urban sanitation management for smarter, cleaner cities.
        </p>
        <p className="text-xs text-gray-400 mt-2">Select your role to continue</p>
      </div>

      {/* Role cards */}
      <div className="flex-1 flex items-start justify-center px-4 pb-12">
        <div className="w-full max-w-3xl">
          {!showWorkerInput && !showAdminInput ? (
            <div className="grid md:grid-cols-3 gap-4">
              {roles.map((option) => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.role}
                    onClick={() => handleRoleSelect(option)}
                    className={`group relative text-left p-6 rounded-2xl border-2 transition-all duration-200 ${option.bgColor} ${option.borderColor} ${
                      selectedRole === option.role ? 'ring-2 ring-offset-2 ring-emerald-500' : ''
                    }`}
                  >
                    <div
                      className={`w-14 h-14 rounded-xl flex items-center justify-center mb-4 bg-white shadow-sm`}
                    >
                      <Icon className={`h-7 w-7 ${option.color}`} />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 mb-1">{option.title}</h3>
                    <p className="text-sm text-gray-600 leading-relaxed">{option.description}</p>
                    <div
                      className={`mt-4 flex items-center gap-1 text-sm font-medium ${option.color} opacity-0 group-hover:opacity-100 transition-opacity`}
                    >
                      Continue <ArrowRight className="h-4 w-4" />
                    </div>
                  </button>
                );
              })}
            </div>
          ) : showWorkerInput ? (
            /* Worker ID input */
            <div className="max-w-md mx-auto">
              <button
                onClick={() => setShowWorkerInput(false)}
                className="text-sm text-gray-500 hover:text-gray-700 mb-4 flex items-center gap-1"
              >
                &larr; Back to role selection
              </button>
              <div className="bg-white rounded-2xl border-2 border-amber-200 p-8 shadow-sm">
                <div className="w-14 h-14 rounded-xl flex items-center justify-center mb-4 bg-amber-50">
                  <HardHat className="h-7 w-7 text-amber-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Worker Login</h3>
                <p className="text-sm text-gray-500 mb-6">
                  Enter your Worker ID to access your task dashboard.
                </p>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Worker ID
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        value={workerId}
                        onChange={(e) => setWorkerId(e.target.value)}
                        placeholder="e.g. W-001"
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none"
                        onKeyDown={(e) => e.key === 'Enter' && handleWorkerLogin()}
                      />
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      Demo IDs: W-001 through W-005
                    </p>
                  </div>

                  <button
                    onClick={handleWorkerLogin}
                    disabled={!workerId.trim()}
                    className="w-full flex items-center justify-center gap-2 py-3 bg-amber-500 text-white font-semibold rounded-xl hover:bg-amber-600 transition disabled:opacity-50"
                  >
                    Enter Dashboard
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* Admin login */
            <div className="max-w-md mx-auto">
              <button
                onClick={() => setShowAdminInput(false)}
                className="text-sm text-gray-500 hover:text-gray-700 mb-4 flex items-center gap-1"
              >
                &larr; Back to role selection
              </button>
              <div className="bg-white rounded-2xl border-2 border-emerald-200 p-8 shadow-sm">
                <div className="w-14 h-14 rounded-xl flex items-center justify-center mb-4 bg-emerald-50">
                  <BarChart3 className="h-7 w-7 text-emerald-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Admin Login</h3>
                <p className="text-sm text-gray-500 mb-6">
                  Municipal authority access to the operations dashboard.
                </p>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Username
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        defaultValue="admin@sanitisense.in"
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl text-sm bg-gray-50 text-gray-500 outline-none"
                        readOnly
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="password"
                        value={adminPass}
                        onChange={(e) => setAdminPass(e.target.value)}
                        placeholder="Enter password"
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                        onKeyDown={(e) => e.key === 'Enter' && handleAdminLogin()}
                      />
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      Demo: use any password
                    </p>
                  </div>

                  <button
                    onClick={handleAdminLogin}
                    disabled={!adminPass.trim()}
                    className="w-full flex items-center justify-center gap-2 py-3 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 transition disabled:opacity-50"
                  >
                    Access Dashboard
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Tech badges */}
          <div className="mt-10 text-center">
            <p className="text-xs text-gray-400 mb-3">Powered by</p>
            <div className="flex items-center justify-center gap-3 flex-wrap">
              {['Amazon Bedrock', 'DynamoDB', 'Lambda', 'Rekognition', 'S3'].map((tech) => (
                <span
                  key={tech}
                  className="text-xs bg-gray-100 text-gray-500 px-2.5 py-1 rounded-full"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
