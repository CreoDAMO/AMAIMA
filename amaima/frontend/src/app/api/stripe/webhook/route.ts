import { NextRequest, NextResponse } from 'next/server';
import { getStripeSync, getUncachableStripeClient } from '@/lib/stripeClient';
import { initStripe } from '@/lib/stripeInit';
import { Pool } from 'pg';

let pool: Pool | null = null;
function getPool() {
  if (!pool) {
    pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 2 });
  }
  return pool;
}

async function updateApiKeyTier(apiKeyId: string, tier: string, stripeCustomerId: string, stripeSubscriptionId: string) {
  const db = getPool();
  await db.query(
    `UPDATE api_keys SET tier = $1, stripe_customer_id = $2, stripe_subscription_id = $3 WHERE id = $4`,
    [tier, stripeCustomerId, stripeSubscriptionId, apiKeyId]
  );
}

async function getTierFromPrice(priceId: string): Promise<string> {
  try {
    const stripe = await getUncachableStripeClient();
    const price = await stripe.prices.retrieve(priceId, { expand: ['product'] });
    const product = price.product as any;
    return product?.metadata?.tier || 'community';
  } catch {
    return 'community';
  }
}

export async function POST(request: NextRequest) {
  try {
    await initStripe();

    const signature = request.headers.get('stripe-signature');
    if (!signature) {
      return NextResponse.json({ error: 'Missing stripe-signature' }, { status: 400 });
    }

    const body = await request.arrayBuffer();
    const payload = Buffer.from(body);

    const sync = await getStripeSync();
    await sync.processWebhook(payload, signature);

    const stripe = await getUncachableStripeClient();
    const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

    if (webhookSecret) {
      const event = stripe.webhooks.constructEvent(payload.toString(), signature, webhookSecret);

      if (event.type === 'checkout.session.completed') {
        const session = event.data.object as any;
        const apiKeyId = session.metadata?.apiKeyId;
        const customerId = session.customer as string;
        const subscriptionId = session.subscription as string;

        if (apiKeyId && subscriptionId) {
          const subscription = await stripe.subscriptions.retrieve(subscriptionId);
          const priceId = subscription.items.data[0]?.price?.id;
          if (priceId) {
            const tier = await getTierFromPrice(priceId);
            await updateApiKeyTier(apiKeyId, tier, customerId, subscriptionId);
            console.log(`Updated API key tier to: ${tier}`);
          }
        }
      }

      if (event.type === 'customer.subscription.updated' || event.type === 'customer.subscription.deleted') {
        const subscription = event.data.object as any;
        const customerId = subscription.customer as string;

        const db = getPool();
        const result = await db.query('SELECT id FROM api_keys WHERE stripe_customer_id = $1', [customerId]);

        if (result.rows.length > 0) {
          const apiKeyId = result.rows[0].id;

          if (event.type === 'customer.subscription.deleted' || subscription.status === 'canceled') {
            await updateApiKeyTier(apiKeyId, 'community', customerId, '');
            console.log('Downgraded API key to community (subscription canceled)');
          } else if (subscription.status === 'active') {
            const priceId = subscription.items?.data?.[0]?.price?.id;
            if (priceId) {
              const tier = await getTierFromPrice(priceId);
              await updateApiKeyTier(apiKeyId, tier, customerId, subscription.id);
              console.log(`Updated API key tier to: ${tier}`);
            }
          }
        }
      }
    }

    return NextResponse.json({ received: true });
  } catch (error: any) {
    console.error('Webhook error:', error.message);
    return NextResponse.json({ error: 'Webhook processing error' }, { status: 400 });
  }
}
