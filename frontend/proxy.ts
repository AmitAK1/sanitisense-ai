/**
 * Next.js Edge Proxy — Route Protection
 *
 * Runs on the server/Edge BEFORE the page renders, so there is zero client-side
 * flash of protected content. Reads the HttpOnly `sanitisense_role` cookie set
 * by /api/auth/login.
 *
 * Protected routes:
 *   /dashboard  → requires role = "admin"
 *   /worker     → requires role = "worker"
 *
 * Unprotected routes (allowed through):
 *   /           homepage
 *   /login      login page
 *   /report     citizen report (no auth required)
 *   /track      citizen tracking (no auth required)
 *   /api/*      API routes (handled by their own logic)
 */
import { NextResponse, type NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const role = request.cookies.get('sanitisense_role')?.value;
    const { pathname } = request.nextUrl;

    // Admin dashboard — requires admin role
    if (pathname.startsWith('/dashboard')) {
        if (role !== 'admin') {
            const loginUrl = new URL('/login', request.url);
            loginUrl.searchParams.set('from', pathname);
            return NextResponse.redirect(loginUrl);
        }
    }

    // Worker dashboard — requires worker role
    if (pathname.startsWith('/worker')) {
        if (role !== 'worker') {
            const loginUrl = new URL('/login', request.url);
            loginUrl.searchParams.set('from', pathname);
            return NextResponse.redirect(loginUrl);
        }
    }

    return NextResponse.next();
}

export const config = {
    // Only run on protected routes — exclude static assets, API routes, etc.
    matcher: ['/dashboard/:path*', '/worker/:path*'],
};
