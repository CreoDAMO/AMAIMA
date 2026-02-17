import { NextRequest, NextResponse } from 'next/server';
import { getUncachableStripeClient } from '@/lib/stripeClient';
import { initStripe } from '@/lib/stripeInit';
import { Pool } from 'pg';

let pool: Pool | null = null;
function getPool() {
  if (!pool) {
    pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 2 });
  }
  return pool;
}

export async function POST(request: NextRequest) {
  try {
    await initStripe();
    const stripe = await getUncachableStripeClient();
    const { priceId, apiKeyId, email } = await request.json();

    if (!priceId) {
      return NextResponse.json({ error: 'priceId is required' }, { status: 400 });
    }

    const db = getPool();
    let customerId: string | null = null;

    if (apiKeyId) {
      const result = await db.query(
        'SELECT stripe_customer_id, user_email FROM api_keys WHERE id = $1',
        [apiKeyId]
      );
      if (result.rows[0]?.stripe_customer_id) {
        customerId = result.rows[0].stripe_customer_id;
      }
    }

    if (!customerId) {
      const customer = await stripe.customers.create({
        email: email || 'user@amaima.ai',
        metadata: { apiKeyId: apiKeyId || 'unknown' },
      });
      customerId = customer.id;

      if (apiKeyId) {
        await db.query(
          'UPDATE api_keys SET stripe_customer_id = $1 WHERE id = $2',
          [customerId, apiKeyId]
        );
      }
    }

    const domains = process.env.REPLIT_DOMAINS?.split(',')[0] || 'localhost:5000';
    const baseUrl = `https://${domains}`;

    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      payment_method_types: ['card'],
      line_items: [{ price: priceId, quantity: 1 }],
      mode: 'subscription',
      success_url: `${baseUrl}/billing?success=true`,
      cancel_url: `${baseUrl}/billing?canceled=true`,
      metadata: { apiKeyId: apiKeyId || '' },
    });

    return NextResponse.json({ url: session.url });
  } catch (error: any) {
    console.error('Checkout error:', error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
