import { NextResponse } from 'next/server';
import { getStripePublishableKey } from '@/lib/stripeClient';

export async function GET() {
  try {
    const key = await getStripePublishableKey();
    return NextResponse.json({ publishableKey: key });
  } catch (error: any) {
    console.error('Publishable key error:', error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
