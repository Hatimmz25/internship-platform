import Link from 'next/link';
import { fetchAPI } from '@/lib/api-client';

interface MatchRow { id: number; score: number; reasons: string[];
  offer: { id: number; title: string; company: string; country: string; canonical_url: string } }

export default async function Dashboard() {
  let matches: MatchRow[] = [];
  let error: string | null = null;
  try { matches = await fetchAPI<MatchRow[]>('/matches'); } catch (e: any) { error = e.message; }
  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Your matches</h1>
        <Link href="/dashboard/preferences" className="text-blue-600 text-sm">Edit preferences</Link>
      </div>
      {error && <p className="text-red-600">{error}</p>}
      {!error && matches.length === 0 && <p className="text-slate-500">No matches yet.</p>}
      {matches.map((m) => (
        <a key={m.id} href={m.offer.canonical_url} target="_blank" rel="noopener noreferrer"
           className="block bg-white border border-slate-200 rounded-lg p-5 hover:border-blue-300">
          <div className="flex justify-between">
            <div><h2 className="font-semibold">{m.offer.title}</h2>
              <p className="text-slate-600 text-sm">{m.offer.company} · {m.offer.country}</p></div>
            <span className="text-blue-700 font-bold">{m.score.toFixed(0)}%</span>
          </div>
          {m.reasons[0] && <p className="text-xs text-slate-500 mt-2">{m.reasons[0]}</p>}
        </a>
      ))}
    </div>
  );
}