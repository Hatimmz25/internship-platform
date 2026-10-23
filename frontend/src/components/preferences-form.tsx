'use client'
import { useFormState, useFormStatus } from 'react-dom';
import { savePreferencesAction } from '@/app/actions/auth';
import { Preference } from '@/types';

function Save() {
  const { pending } = useFormStatus();
  return <button type="submit" disabled={pending}
    className="bg-blue-600 text-white px-6 py-2 rounded-md text-sm disabled:opacity-50">
    {pending ? 'Saving…' : 'Save Preferences'}</button>;
}

const input = 'w-full border border-slate-300 rounded-md px-3 py-2 text-sm';

export default function PreferencesForm({ pref }: { pref: Preference }) {
  const [state, action] = useFormState(savePreferencesAction, null);
  return (
    <form action={action} className="space-y-6 bg-white border border-slate-200 rounded-xl p-8">
      {state?.error && <p className="text-red-600 text-sm">{state.error}</p>}
      {state?.ok && <p className="text-green-600 text-sm">Saved.</p>}
      <label className="block text-sm font-medium">Target roles (comma separated)
        <input name="target_roles" defaultValue={pref.target_roles.join(', ')} className={input} /></label>
      <label className="block text-sm font-medium">Preferred countries
        <input name="preferred_countries" defaultValue={pref.preferred_countries.join(', ')} className={input} /></label>
      <label className="block text-sm font-medium">Skills
        <textarea name="skills" rows={3} defaultValue={pref.skills.join(', ')} className={input} /></label>
      <label className="block text-sm font-medium">Alert frequency
        <select name="alert_frequency" defaultValue={pref.alert_frequency} className={input}>
          <option value="INSTANT">Real-time</option><option value="DAILY">Daily digest</option>
          <option value="WEEKLY">Weekly (not implemented yet)</option><option value="OFF">Paused</option>
        </select></label>
      <label className="block text-sm font-medium">Minimum match score (0-100)
        <input name="min_relevance_score" type="number" min={0} max={100}
          defaultValue={pref.min_relevance_score} className={input} /></label>
      <div className="flex justify-end"><Save /></div>
    </form>
  );
}