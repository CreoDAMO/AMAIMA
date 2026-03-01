/** @type {import('next').NextConfig} */

const nextConfig = {
  // ── Memory optimization ────────────────────────────────────────────────────
  // swcMinify: false uses Terser which is more memory-efficient than SWC
  // during the build phase on constrained VPS environments.
  swcMinify: false,

  // Disable source maps in production — saves ~200MB during build
  productionBrowserSourceMaps: false,

  // Limit webpack parallelism to 1 CPU during build.
  // Combined with NODE_OPTIONS=--max-old-space-size=256 this keeps
  // the Next.js build under 500MB and prevents OOM kills.
  webpack: (config, { dev }) => {
    if (!dev) {
      config.parallelism = 1;
    }
    return config;
  },

  // ── API proxy ──────────────────────────────────────────────────────────────
  // All /v1/* and /health requests from the browser are proxied to the
  // FastAPI backend running on localhost:8000 inside the same container.
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    return [
      {
        source: "/v1/:path*",
        destination: `${backendUrl}/v1/:path*`,
      },
      {
        source: "/health",
        destination: `${backendUrl}/health`,
      },
      {
        source: "/ws/:path*",
        destination: `${backendUrl}/ws/:path*`,
      },
    ];
  },

  // ── Security headers ───────────────────────────────────────────────────────
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },

  // ── Output tracing ─────────────────────────────────────────────────────────
  // Silences the duplicate lockfile warning during Docker builds
  outputFileTracingRoot: require("path").join(__dirname, "../../"),
};

module.exports = nextConfig;
