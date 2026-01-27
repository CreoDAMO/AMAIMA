import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from './core/components/shared/Providers';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'AMAIMA - Advanced AI Intelligence',
  description: 'Next-generation AI query system with intelligent model routing',
  keywords: ['AI', 'Machine Learning', 'Query System', 'Neural Networks'],
  icons: {
    icon: [
      {
        url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:%2306b6d4"/><stop offset="100%" style="stop-color:%23a855f7"/></linearGradient></defs><circle cx="50" cy="50" r="45" fill="url(%23grad)"/><path d="M50 20 L50 35 M50 65 L50 80 M20 50 L35 50 M65 50 L80 50 M28 28 L38 38 M62 62 L72 72 M72 28 L62 38 M38 62 L28 72" stroke="white" stroke-width="4" stroke-linecap="round"/><circle cx="50" cy="50" r="12" fill="white"/></svg>',
        type: 'image/svg+xml',
      },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
