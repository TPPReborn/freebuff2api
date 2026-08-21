// worker.js
var worker_default = {
  async fetch(request, env, ctx) {
    const target = request.headers.get("x-relay-target");
    const relayPath = request.headers.get("x-relay-path") || "/";
    if (!target) {
      return new Response(JSON.stringify({ error: "Missing x-relay-target header" }), {
        status: 400,
        headers: { "content-type": "application/json" }
      });
    }
    const targetUrl = target.replace(/\/$/, "") + relayPath;
    const newRequestInit = {
      method: request.method,
      headers: new Headers(request.headers)
    };
    if (request.method !== "GET" && request.method !== "HEAD") {
      newRequestInit.body = request.body;
      newRequestInit.duplex = "half";
    }
    newRequestInit.headers.delete("x-relay-target");
    newRequestInit.headers.delete("x-relay-path");
    newRequestInit.headers.delete("host");
    newRequestInit.headers.delete("origin");
    newRequestInit.headers.delete("referer");
    for (const key of [...newRequestInit.headers.keys()]) {
      if (key.toLowerCase().startsWith("cf-")) {
        newRequestInit.headers.delete(key);
      }
    }
    for (const key of ["x-forwarded-for", "x-forwarded-proto", "x-real-ip", "x-vercel-id", "x-vercel-forwarded-for"]) {
      newRequestInit.headers.delete(key);
    }
    const ua = (newRequestInit.headers.get("user-agent") || "").toLowerCase();
    if (ua.includes("python") || ua.includes("curl") || ua.includes("node-fetch") || ua.includes("go-http")) {
      newRequestInit.headers.set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36");
    }
    if (target.includes("codebuff.com") || target.includes("freebuff.com")) {
      if (!newRequestInit.headers.has("x-freebuff-sdk-version")) {
        newRequestInit.headers.set("x-freebuff-sdk-version", "0.0.141");
      }
      if (!newRequestInit.headers.has("x-freebuff-client-type")) {
        newRequestInit.headers.set("x-freebuff-client-type", "cli");
      }
    }
    try {
      const response = await fetch(targetUrl, newRequestInit);
      return new Response(response.body, {
        status: response.status,
        headers: response.headers
      });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 502,
        headers: { "content-type": "application/json" }
      });
    }
  }
};
export {
  worker_default as default
};
//# sourceMappingURL=worker.js.map
