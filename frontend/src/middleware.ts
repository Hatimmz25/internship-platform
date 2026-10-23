import { NextResponse, type NextRequest } from 'next/server';
export function middleware(req: NextRequest) {
  if (!req.cookies.has('token')) return NextResponse.redirect(new URL('/login', req.url));
}
export const config = { matcher: ['/dashboard/:path*'] };