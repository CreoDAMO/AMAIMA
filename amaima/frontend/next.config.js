/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    poweredByHeader: false,
    
    allowedDevOrigins: [
        'https://44a1d514-2a8f-40f9-aa0d-80b18eac2070-00-3dk80d89fmri4.janeway.replit.dev',
        '127.0.0.1',
        'localhost',
    ],
    
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
    
    async headers() {
        return [
            {
                source: '/:path*',
                headers: [
                    {
                        key: 'X-Content-Type-Options',
                        value: 'nosniff',
                    },
                    {
                        key: 'Referrer-Policy',
                        value: 'strict-origin-when-cross-origin',
                    },
                    {
                        key: 'Cache-Control',
                        value: 'no-cache, no-store, must-revalidate',
                    },
                ],
            },
        ];
    },
    
    webpack: (config, { isServer }) => {
        if (!isServer) {
            config.resolve.fallback = {
                ...config.resolve.fallback,
                fs: false,
                path: false,
            };
        }
        
        return config;
    },
    
    experimental: {
        optimizePackageImports: ['lucide-react', 'framer-motion'],
    },
    turbopack: {},
};

module.exports = nextConfig;
