import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

function sanitizeBillingPath(rawPath: string | null): string | null {
  if (!rawPath) {
    return null;
  }
  // Disallow leading slashes and path traversal, and restrict characters.
  if (rawPath.startsWith('/') || rawPath.includes('..')) {
    return null;
  }
  // Allow alphanumerics, dashes, underscores, and forward slashes for nested resources.
  const validPathPattern = /^[A-Za-z0-9/_-]+$/;
  if (!validPathPattern.test(rawPath)) {
    return null;
  }
  return rawPath;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const rawPath = searchParams.get('path');
  const path = sanitizeBillingPath(rawPath);
  const apiKey = request.headers.get('x-api-key') || '';

  if (!path) {
    return NextResponse.json({ error: 'Invalid path parameter' }, { status: 400 });
  }

  // Do not forward the "path" query parameter to the backend.
  const forwardedParams = new URLSearchParams(searchParams.toString());
  forwardedParams.delete('path');

  try {
    const queryString = forwardedParams.toString();
    const url = queryString
      ? `${BACKEND_URL}/v1/billing/${path}?${queryString}`
      : `${BACKEND_URL}/v1/billing/${path}`;
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
  const path = sanitizeBillingPath(rawPath);
  if (!path) {
    return NextResponse.json({ error: 'Invalid path parameter' }, { status: 400 });
  }

  const apiKey = request.headers.get('x-api-key') || '';

  try {
    const body = await request.json();
    const url = `${BACKEND_URL}/v1/billing/${path}`;
    const res = await fetch(url, {
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
