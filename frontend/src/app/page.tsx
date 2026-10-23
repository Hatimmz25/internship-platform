import Link from 'next/link';
import { fetchAPI } from '@/lib/api-client';
import { AnalyticsOverview } from '@/types';
import { Search, MapPin, Code2, Zap } from 'lucide-react';

export default async function Home() {
  let stats: AnalyticsOverview | null = null;
  try {
    stats = await fetchAPI<AnalyticsOverview>('/analytics/overview', { next: { revalidate: 3600 } });
  } catch (e) {
    console.error("Failed to fetch analytics");
  }

  return (
    <div className="bg-slate-50">
      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32 flex flex-col items-center text-center">
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 mb-6">
          Find your perfect <span className="text-blue-600">PFE Internship</span> automatically.
        </h1>
        <p className="text-lg md:text-xl text-slate-600 max-w-3xl mb-10 leading-relaxed">
          We aggregate opportunities in AI, Data Science, and Engineering across Europe. Set your preferences once and get real-time email alerts when matching roles drop.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 w-full justify-center">
          <form action="/offers" className="flex w-full max-w-md shadow-sm">
            <div className="relative flex-grow">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-slate-400" />
              </div>
              <input
                type="text"
                name="search"
                className="block w-full pl-10 pr-3 py-3 border border-slate-300 rounded-l-md leading-5 bg-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 sm:text-sm"
                placeholder="Search keywords (e.g. PyTorch, NLP...)"
              />
            </div>
            <button type="submit" className="bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-r-md font-medium transition-colors">
              Search
            </button>
          </form>
          <Link href="/register" className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-md font-medium shadow-sm transition-colors flex items-center justify-center">
            Create Alert
          </Link>
        </div>
      </section>

      {/* Database Stats Section */}
      {stats && (
        <section className="bg-white border-y border-slate-200 py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-2xl font-bold text-center text-slate-900 mb-10">Currently tracking across Europe</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-slate-50 rounded-xl p-6 border border-slate-100 flex flex-col items-center text-center">
                <Zap className="h-8 w-8 text-blue-500 mb-4" />
                <span className="text-4xl font-bold text-slate-900">{stats.total_offers}</span>
                <span className="text-sm font-medium text-slate-500 uppercase tracking-wider mt-2">Active Opportunities</span>
              </div>
              <div className="bg-slate-50 rounded-xl p-6 border border-slate-100 flex flex-col items-center text-center">
                <Code2 className="h-8 w-8 text-blue-500 mb-4" />
                <div className="flex flex-wrap justify-center gap-2 mt-2">
                  {stats.top_skills.slice(0, 5).map(skill => (
                    <span key={skill} className="bg-white border border-slate-200 px-3 py-1 rounded-full text-xs font-semibold text-slate-700">{skill}</span>
                  ))}
                </div>
                <span className="text-sm font-medium text-slate-500 uppercase tracking-wider mt-4">Top Demanded Skills</span>
              </div>
              <div className="bg-slate-50 rounded-xl p-6 border border-slate-100 flex flex-col items-center text-center">
                <MapPin className="h-8 w-8 text-blue-500 mb-4" />
                <span className="text-lg font-semibold text-slate-800 mt-2">{stats.top_countries.slice(0,3).join(', ')}</span>
                <span className="text-sm font-medium text-slate-500 uppercase tracking-wider mt-4">Top Destinations</span>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}