import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Navigation from '@/components/navigation';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'InternshipRadar AI | Find Your PFE',
  description: 'Automated internship discovery and matching for Data, AI, and Engineering students.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-50 min-h-screen flex flex-col text-slate-900`}>
        <Navigation />
        <main className="flex-grow">{children}</main>
        <footer className="bg-white border-t border-slate-200 mt-auto py-8">
          <div className="max-w-7xl mx-auto px-4 text-center text-slate-500 text-sm flex flex-col md:flex-row justify-between items-center">
            <p>&copy; {new Date().getFullYear()} InternshipRadar AI. All rights reserved.</p>
            <p className="mt-2 md:mt-0">Listings are sourced compliantly from public institutional feeds.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}