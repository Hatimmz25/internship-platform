export interface User {
  id: number;
  email: string;
  role: 'USER' | 'ADMIN' | 'SUBSCRIBER';
  is_active: boolean;
  created_at: string;
}

export interface InternshipOffer {
  id: number;
  source_id: number;
  canonical_url: string;
  title: string;
  company: string;
  location_raw: string | null;
  country: string | null;
  workplace_type: string | null; // remote | hybrid | onsite | on_site | unknown
  internship_type: string | null; // pfe | summer | off_graduate | general | standard
  description: string | null;
  required_skills: string[] | null;
  languages: string[] | null;
  published_at?: string | null;
  first_seen_at: string;
}

export interface Preference {
  target_roles: string[];
  preferred_countries: string[];
  preferred_cities: string[];
  workplace_types: string[];
  internship_types: string[];
  skills: string[];
  preferred_languages: string[];
  keywords: string[];
  exclusion_keywords: string[];
  alert_frequency: 'INSTANT' | 'DAILY' | 'WEEKLY' | 'OFF';
  min_relevance_score: number;
}

export interface AnalyticsOverview {
  total_offers: number;
  top_skills: string[];
  top_countries: string[];
}