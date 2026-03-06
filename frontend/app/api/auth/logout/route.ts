/**
 * POST /api/auth/logout
 * Clears the session cookies by setting Max-Age=0.
 * Call this from a logout button; then redirect to /login on the client.
 */
export async function POST() {
    const clearCookie = `HttpOnly; SameSite=Lax; Secure; Path=/; Max-Age=0`;

    const headers = new Headers({ 'Content-Type': 'application/json' });
    headers.append('Set-Cookie', `sanitisense_role=; ${clearCookie}`);
    headers.append('Set-Cookie', `sanitisense_worker_id=; ${clearCookie}`);

    return new Response(JSON.stringify({ ok: true }), { status: 200, headers });
}
