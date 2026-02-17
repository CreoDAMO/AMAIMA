import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

// Allow-list of permitted biology endpoints to prevent SSRF-style abuse.
const ALLOWED_BIOLOGY_ENDPOINTS = new Set(['query']);

export async function POST(request: Request) {
  try {
    const url = new URL(request.url);
    const endpoint = url.searchParams.get('endpoint') || 'query';
    const safeEndpoint = ALLOWED_BIOLOGY_ENDPOINTS.has(endpoint) ? endpoint : 'query';
    const formData = await request.formData();

    const response = await fetch(`${BACKEND_URL}/v1/biology/${safeEndpoint}`, {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Biology service unavailable' }, { status: 503 });
  }
}

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/v1/biology/capabilities`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Biology service unavailable' }, { status: 503 });
  }
}
