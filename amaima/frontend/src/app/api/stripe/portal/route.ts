import { NextRequest, NextResponse } from 'next/server';
import { getUncachableStripeClient } from '@/lib/stripeClient';

export async function POST(request: NextRequest) {
  try {
    const stripe = await getUncachableStripeClient();
    const { customerId } = await request.json();

    if (!customerId) {
      return NextResponse.json({ error: 'customerId is required' }, { status: 400 });
    }

    const domains = process.env.REPLIT_DOMAINS?.split(',')[0] || 'localhost:5000';
    const returnUrl = `https://${domains}/billing`;

    const session = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: returnUrl,
    });

    return NextResponse.json({ url: session.url });
  } catch (error: any) {
    console.error('Portal error:', error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
