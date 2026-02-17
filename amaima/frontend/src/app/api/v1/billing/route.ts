import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const ALLOWED_BILLING_PATHS: Record<string, string> = {
  'usage': `${BACKEND_URL}/v1/billing/usage`,
  'tiers': `${BACKEND_URL}/v1/billing/tiers`,
  'api-keys': `${BACKEND_URL}/v1/billing/api-keys`,
  'update-tier': `${BACKEND_URL}/v1/billing/update-tier`,
};

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const rawPath = searchParams.get('path');
  const apiKey = request.headers.get('x-api-key') || '';

  if (!rawPath || !ALLOWED_BILLING_PATHS[rawPath]) {
    return NextResponse.json({ error: 'Invalid path parameter' }, { status: 400 });
  }

  const targetUrl = ALLOWED_BILLING_PATHS[rawPath]!;

  const forwardedParams = new URLSearchParams(searchParams.toString());
  forwardedParams.delete('path');

  try {
    const queryString = forwardedParams.toString();
    const url = queryString ? `${targetUrl}?${queryString}` : targetUrl;
    const res = await fetch(url, {
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const rawPath = searchParams.get('path');

  if (!rawPath || !ALLOWED_BILLING_PATHS[rawPath]) {
    return NextResponse.json({ error: 'Invalid path parameter' }, { status: 400 });
  }

  const targetUrl = ALLOWED_BILLING_PATHS[rawPath]!;
  const apiKey = request.headers.get('x-api-key') || '';

  try {
    const body = await request.json();
    const res = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
