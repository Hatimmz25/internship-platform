import { fetchAPI } from '@/lib/api-client';
import { InternshipOffer } from '@/types';
import { MapPin, Briefcase, Calendar, ChevronRight } from 'lucide-react';

export default async function OffersPage({
  searchParams,
}: {
  searchParams: { search?: string; country?: string };
}) {
  const query = new URLSearchParams();
  if (searchParams.search) query.append('search', searchParams.search);
  if (searchParams.country) query.append('country', searchParams.country);

  let offers: InternshipOffer[] = [];
  try {
    offers = await fetchAPI<InternshipOffer[]>(`/offers?${query.toString()}`);
  } catch (error) {
    return <div className="text-center py-20 text-red-600">Failed to load offers. Please try again later.</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Internship Discovery</h1>
          <p className="text-slate-500 mt-1">Showing {offers.length} recent opportunities matching your criteria.</p>
        </div>
      </div>

      {offers.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-lg p-12 text-center">
          <h3 className="text-lg font-medium text-slate-900">No offers found</h3>
          <p className="text-slate-500 mt-2">Try adjusting your search criteria or removing filters.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {offers.map((offer) => (
            <a
              key={offer.id}
              href={offer.canonical_url}
              target="_blank"
              rel="noopener noreferrer"
              className="block group"
            >
              <div className="bg-white border border-slate-200 rounded-lg p-6 hover:shadow-md hover:border-blue-300 transition-all">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                      {offer.title}
                    </h2>
                    <p className="text-slate-600 font-medium mt-1">{offer.company}</p>

                    <div className="flex flex-wrap items-center gap-4 mt-4 text-sm text-slate-500">
                      {offer.location_raw && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-4 w-4" /> {offer.location_raw}
                        </span>
                      )}
                      {offer.workplace_type && (
                        <span className="flex items-center gap-1">
                          <Briefcase className="h-4 w-4" /> {offer.workplace_type.replace('_', ' ')}
                        </span>
                      )}
                      {offer.published_at && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" /> {new Date(offer.published_at).toLocaleDateString()}
                        </span>
                      )}
                      {offer.internship_type && (
                        <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs font-semibold uppercase">
                          {offer.internship_type}
                        </span>
                      )}
                    </div>

                    {(offer.required_skills ?? []).length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {(offer.required_skills ?? []).map((skill) => (
                          <span key={skill} className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md text-xs font-medium">
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="hidden md:flex items-center justify-center h-10 w-10 bg-slate-50 rounded-full group-hover:bg-blue-50 transition-colors">
                    <ChevronRight className="h-5 w-5 text-slate-400 group-hover:text-blue-600" />
                  </div>
                </div>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}