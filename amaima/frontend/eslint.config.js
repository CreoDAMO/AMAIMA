// eslint.config.js - Modern flat config for Next.js
import nextPlugin from '@next/eslint-plugin-next';

export default [
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    plugins: {
      '@next/next': nextPlugin,
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs['core-web-vitals'].rules,
      // Add custom rules if needed, e.g., 'no-console': 'warn'
    },
  },
];