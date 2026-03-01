/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
    reactStrictMode: true,
    poweredByHeader: false,
    
    allowedDevOrigins: ['*', '*.replit.dev', '*.spock.replit.dev', '*.repl.co', '*.kirk.replit.dev', '*.janeway.replit.dev', '127.0.0.1'],
    
    env: {
        NEXT_PUBLIC_APP_NAME: 'AMAIMA',
        NEXT_PUBLIC_APP_VERSION: '5.0.0',
    },
    
    images: {
        formats: ['image/avif', 'image/webp'],
        deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
        remotePatterns: [
            {
                protocol: 'https',
                hostname: '**',
            },
        ],
    },
    
  // Combined with NODE_OPTIONS=--max-old-space-size=256 this keeps
  // the Next.js build under 500MB and prevents OOM kills.
  webpack: (config, { dev, isServer }) => {
    if (!dev) {
      config.parallelism = 1;
    }
    if (!isServer) {
        config.resolve.fallback = {
            ...config.resolve.fallback,
            fs: false,
            path: false,
        };
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
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
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
    
    experimental: {
        optimizePackageImports: ['lucide-react', 'framer-motion'],
    },
    outputFileTracingRoot: path.join(__dirname, '../../'),
    turbopack: {},
};

module.exports = nextConfig;
