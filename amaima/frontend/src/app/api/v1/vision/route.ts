import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const ALLOWED_VISION_ENDPOINTS = new Set<string>([
  'reason',
  'capabilities',
]);

export async function POST(request: Request) {
  try {
    const url = new URL(request.url);
    const rawEndpoint = url.searchParams.get('endpoint');
    const endpoint = rawEndpoint ?? 'reason';

    if (!ALLOWED_VISION_ENDPOINTS.has(endpoint)) {
      return NextResponse.json({ error: 'Invalid endpoint' }, { status: 400 });
    }

    const formData = await request.formData();

    const response = await fetch(`${BACKEND_URL}/v1/vision/${endpoint}`, {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Vision service unavailable' }, { status: 503 });
  }
}

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/v1/vision/capabilities`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Vision service unavailable' }, { status: 503 });
  }
}
