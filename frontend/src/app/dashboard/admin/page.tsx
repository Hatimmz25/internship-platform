import { fetchAPI } from '@/lib/api-client';
import { DashboardKPIs, ScrapingSource, ScrapingRun } from '@/types/admin';
import TriggerButton from '@/components/trigger-button';
import { Activity, Database, Users, AlertTriangle, RefreshCw, CheckCircle } from 'lucide-react';

export default async function AdminDashboard() {
  let kpis: DashboardKPIs | null = null;
  let sources: ScrapingSource[] = [];
  let runs: ScrapingRun[] = [];
  let error: string | null = null;

  try {
    [kpis, sources, runs] = await Promise.all([
      fetchAPI<DashboardKPIs>('/admin/kpis'),
      fetchAPI<ScrapingSource[]>('/admin/sources'),
      fetchAPI<ScrapingRun[]>('/admin/runs?limit=10'),
    ]);
  } catch (err: any) {
    error = err.message || 'Failed to load administrative data. Are you an admin?';
  }

  if (error || !kpis) {
    return <div className="p-8 text-center text-red-600 bg-red-50 m-4 rounded-lg">{error}</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Platform Command Center</h1>
        <p className="text-slate-500 mt-2">Database-backed metrics, scraping controls, and system health.</p>
      </div>

      {/* KPIs */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <Database className="h-10 w-10 text-blue-500 bg-blue-50 p-2 rounded-lg" />
          <div>
            <p className="text-sm font-medium text-slate-500">Active Opportunities</p>
            <p className="text-2xl font-bold text-slate-900">{kpis.total_active_offers}</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <Users className="h-10 w-10 text-green-500 bg-green-50 p-2 rounded-lg" />
          <div>
            <p className="text-sm font-medium text-slate-500">Active Subscribers</p>
            <p className="text-2xl font-bold text-slate-900">{kpis.active_subscribers}</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <Activity className="h-10 w-10 text-purple-500 bg-purple-50 p-2 rounded-lg" />
          <div>
            <p className="text-sm font-medium text-slate-500">7-Day Discovery</p>
            <p className="text-2xl font-bold text-slate-900">+{kpis.recent_offers_7d}</p>
          </div>
        </div>
      </section>

      {/* Sources */}
      <section className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-200 bg-slate-50">
          <h2 className="text-lg font-bold text-slate-800">Scraping Sources</h2>
        </div>
        <div className="divide-y divide-slate-100">
          {sources.map((source) => (
            <div key={source.id} className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-slate-900">{source.name}</h3>
                  <span
                    className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                      source.is_active ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {source.is_active ? 'Active' : 'Disabled'}
                  </span>
                </div>
                <p className="text-sm text-slate-500 mt-1">{source.base_url}</p>
              </div>
              <TriggerButton sourceId={source.id} disabled={!source.is_active} />
            </div>
          ))}
        </div>
      </section>

      {/* Recent runs */}
      <section className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-200 bg-slate-50">
          <h2 className="text-lg font-bold text-slate-800">Recent Scraping Execution History</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-3 font-medium">Source</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Extracted (New)</th>
                <th className="px-6 py-3 font-medium">Started At</th>
                <th className="px-6 py-3 font-medium">Duration</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {runs.map((run) => (
                <tr key={run.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-medium text-slate-900">{run.source_name}</td>
                  <td className="px-6 py-4">
                    {run.status === 'SUCCESS' ? (
                      <span className="flex items-center gap-1 text-green-600 font-medium">
                        <CheckCircle className="h-4 w-4" /> Success
                      </span>
                    ) : run.status === 'FAILED' ? (
                      <span className="flex items-center gap-1 text-red-600 font-medium">
                        <AlertTriangle className="h-4 w-4" /> Failed
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-blue-600 font-medium">
                        <RefreshCw className="h-4 w-4" /> Pending
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-slate-600">
                    {run.items_found} <span className="text-green-600 font-medium">(+{run.items_new})</span>
                  </td>
                  <td className="px-6 py-4 text-slate-500">{new Date(run.started_at).toLocaleString()}</td>
                  <td className="px-6 py-4 text-slate-500">
                    {run.duration_seconds != null ? `${run.duration_seconds.toFixed(1)}s` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}