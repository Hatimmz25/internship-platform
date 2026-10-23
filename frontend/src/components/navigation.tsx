import Link from 'next/link';
import { cookies } from 'next/headers';
import { Briefcase, User, LogOut } from 'lucide-react';
import { logoutAction } from '@/app/actions/auth';

export default function Navigation() {
  const cookieStore = cookies();
  const isAuthenticated = cookieStore.has('token');

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center gap-2">
              <Briefcase className="h-6 w-6 text-blue-600" />
              <span className="font-bold text-xl text-slate-900 tracking-tight">
                InternshipRadar<span className="text-blue-600">.ai</span>
              </span>
            </Link>
            <div className="hidden md:flex ml-10 space-x-8">
              <Link href="/offers" className="text-slate-600 hover:text-slate-900 px-3 py-2 text-sm font-medium transition-colors">
                Discover Offers
              </Link>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="text-slate-600 hover:text-blue-600 p-2 flex items-center gap-2 text-sm font-medium transition-colors">
                  <User className="h-4 w-4" /> Dashboard
                </Link>
                <form action={logoutAction}>
                  <button type="submit" className="text-slate-600 hover:text-red-600 p-2 flex items-center gap-2 text-sm font-medium transition-colors">
                    <LogOut className="h-4 w-4" /> Sign Out
                  </button>
                </form>
              </>
            ) : (
              <>
                <Link href="/login" className="text-slate-600 hover:text-slate-900 px-3 py-2 text-sm font-medium transition-colors">
                  Sign In
                </Link>
                <Link href="/register" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors shadow-sm">
                  Get Alerts
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}