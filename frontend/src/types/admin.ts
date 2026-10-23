export interface DashboardKPIs {
  total_active_offers: number;
  recent_offers_7d: number;
  active_subscribers: number;
  active_sources: number;
  pending_notifications: number;
  failed_notifications: number;
}

export interface ScrapingSource {
  id: number;
  name: string;
  slug: string;
  base_url: string;
  is_active: boolean;
  rate_limit_rps: number;
  created_at: string;
}

export interface ScrapingRun {
  id: number;
  source_name: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILED';
  items_found: number;
  items_new: number;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
  error_log: string | null;
}