/**
 * POST /api/auth/login
 * Sets HttpOnly session cookie server-side — never exposed to client JS.
 * middleware.ts reads this cookie on the Edge for zero-flicker route protection.
 */
export async function POST(request: Request) {
    const body = await request.json().catch(() => ({}));
    const { role, workerId, password } = body as {
        role: string;
        workerId?: string;
        password?: string;
    };

    // ── Demo validation ──────────────────────────────────────────────────────
    if (role === 'admin') {
        if (!password?.trim()) {
            return Response.json({ error: 'Password required' }, { status: 401 });
        }
        // Demo: any non-empty password accepted
    } else if (role === 'worker') {
        if (!workerId?.trim()) {
            return Response.json({ error: 'Worker ID required' }, { status: 401 });
        }
    } else if (role === 'citizen') {
        // Citizens go straight to /report — no session needed
    } else {
        return Response.json({ error: 'Invalid role' }, { status: 400 });
    }

    // ── Build secure cookie string ───────────────────────────────────────────
    // HttpOnly: prevents JS access (XSS protection)
    // SameSite=Lax: CSRF protection while allowing normal navigation
    // Secure: only sent over HTTPS (ignored on http://localhost by design)
    // Max-Age=86400: 24-hour session
    const cookieBase = `HttpOnly; SameSite=Lax; Secure; Path=/; Max-Age=86400`;

    const headers = new Headers({ 'Content-Type': 'application/json' });
    headers.append('Set-Cookie', `sanitisense_role=${role}; ${cookieBase}`);

    if (role === 'worker' && workerId) {
        // worker_id is not sensitive — set separately (also HttpOnly for consistency)
        headers.append(
            'Set-Cookie',
            `sanitisense_worker_id=${workerId.trim()}; ${cookieBase}`
        );
    }

    return new Response(JSON.stringify({ ok: true, role }), {
        status: 200,
        headers,
    });
}
