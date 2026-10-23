'use client'

import { useState, useTransition } from 'react';
import { Play } from 'lucide-react';
import { triggerScrapeAction } from '@/app/actions/auth';

export default function TriggerButton({ sourceId, disabled }: { sourceId: number; disabled?: boolean }) {
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);

  const onClick = () => {
    setMessage(null);
    startTransition(async () => {
      const result = await triggerScrapeAction(sourceId);
      setMessage(result?.error ? `Failed: ${result.error}` : 'Scrape queued.');
    });
  };

  return (
    <div className="flex items-center gap-3">
      {message && <span className="text-xs text-slate-500">{message}</span>}
      <button
        type="button"
        onClick={onClick}
        disabled={disabled || pending}
        className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-sm font-medium transition-colors disabled:opacity-50"
      >
        <Play className="h-4 w-4" /> {pending ? 'Queuing...' : 'Force Run'}
      </button>
    </div>
  );
}