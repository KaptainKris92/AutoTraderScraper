export async function onRequest({ request, env }) {
  try {
    let origin = env.RAILWAY_ORIGIN;
    if (!origin) {
      return new Response("Missing RAILWAY_ORIGIN", { status: 500 });
    }
    // Normalize origin (no trailing slash)
    origin = origin.replace(/\/+$/, "");

    const url = new URL(request.url);

    // This function lives at /api/*, and Flask expects /api/* too.
    // So we forward the full path as-is.
    const target = `${origin}${url.pathname}${url.search}`;

    // Fast-path OPTIONS (rarely needed when proxying same-origin, but harmless)
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204 });
    }

    // Clone request to the new URL
    const forwardReq = new Request(target, request);

    // Optional: drop problematic hop-by-hop headers
    const headers = new Headers(forwardReq.headers);
    headers.delete("host");
    headers.delete("content-length"); // body may be re-chunked

    const resp = await fetch(forwardReq, {
      headers,
      redirect: "follow",
    });

    // Pass-through response
    // (If you want to tweak caching, you can wrap headers here.)
    return new Response(resp.body, {
      status: resp.status,
      headers: resp.headers,
    });
  } catch (err) {
    // Helpful error for debugging in CF logs
    return new Response(`Proxy error: ${err?.message || err}`, { status: 502 });
  }
}
