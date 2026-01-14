/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    reactStrictMode: true,
    poweredByHeader: false,

    // Environment variables exposed to client
    env: {
        NEXT_PUBLIC_APP_NAME: 'AMAIMA',
        NEXT_PUBLIC_APP_VERSION: '5.0.0',
    },

    // Image optimization
    images: {
        formats: ['image/avif', 'image/webp'],
        deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    },

    // Headers for security
    async headers() {
        return [
            {
                source: '/:path*',
                headers: [
                    {
                        key: 'X-Frame-Options',
                        value: 'SAMEORIGIN',
                    },
                    {
                        key: 'X-Content-Type-Options',
                        value: 'nosniff',
                    },
                    {
                        key: 'X-XSS-Protection',
                        value: '1; mode=block',
                    },
                    {
                        key: 'Referrer-Policy',
                        value: 'strict-origin-when-cross-origin',
                    },
                    {
                        key: 'Permissions-Policy',
                        value: 'camera=(), microphone=(), geolocation=()',
                    },
                ],
            },
        ];
    },

    // Redirects
    async redirects() {
        return [
            {
                source: '/login',
                destination: '/auth/login',
                permanent: true,
            },
            {
                source: '/register',
                destination: '/auth/register',
                permanent: true,
            },
        ];
    },

    // Webpack configuration
    webpack: (config, { isServer }) => {
        // TensorFlow.js configuration
        if (!isServer) {
            config.resolve.fallback = {
                ...config.resolve.fallback,
                fs: false,
                path: false,
            };
        }

        return config;
    },

    // Experimental features
    experimental: {
        optimizePackageImports: ['@/components/ui', 'lucide-react', 'framer-motion'],
    },
};

module.exports = nextConfig;
