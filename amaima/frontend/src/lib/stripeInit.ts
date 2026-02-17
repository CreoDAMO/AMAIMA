import { runMigrations } from 'stripe-replit-sync';
import { getStripeSync } from './stripeClient';

let initialized = false;

export async function initStripe() {
  if (initialized) return;

  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    console.warn('DATABASE_URL not set, skipping Stripe initialization');
    return;
  }

  try {
    console.log('Initializing Stripe schema...');
    await runMigrations({ databaseUrl });
    console.log('Stripe schema ready');

    const stripeSync = await getStripeSync();

    const domains = process.env.REPLIT_DOMAINS?.split(',')[0];
    if (domains) {
      console.log('Setting up managed webhook...');
      const webhookBaseUrl = `https://${domains}`;
      const { webhook } = await stripeSync.findOrCreateManagedWebhook(
        `${webhookBaseUrl}/api/stripe/webhook`
      );
      console.log(`Webhook configured: ${webhook.url}`);
    }

    stripeSync.syncBackfill()
      .then(() => console.log('Stripe data synced'))
      .catch((err: any) => console.error('Error syncing Stripe data:', err));

    initialized = true;
  } catch (error) {
    console.error('Failed to initialize Stripe:', error);
  }
}
