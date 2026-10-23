import { fetchAPI } from '@/lib/api-client';
import { Preference } from '@/types';
import PreferencesForm from '@/components/preferences-form';
import { Settings, AlertCircle } from 'lucide-react';

export default async function PreferencesPage() {
  let pref: Preference | null = null;
  let error: string | null = null;

  try {
    pref = await fetchAPI<Preference>('/preferences');
  } catch (e: any) {
    error = e.message;
  }

  if (error || !pref) {
    return (
      <div className="max-w-3xl mx-auto p-6 mt-10 bg-red-50 text-red-600 rounded-lg flex items-center gap-3">
        <AlertCircle /> Failed to load preferences. Make sure you are signed in.
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <div className="mb-8 border-b border-slate-200 pb-5">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Settings className="h-6 w-6 text-blue-600" /> Alert Preferences
        </h1>
        <p className="text-slate-500 mt-2">Configure how the ranking engine matches you to opportunities.</p>
      </div>

      <PreferencesForm pref={pref} />
    </div>
  );
}