import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const ENDPOINT_URLS: Record<string, string> = {
  reason: `${BACKEND_URL}/v1/vision/reason`,
  'analyze-image': `${BACKEND_URL}/v1/vision/analyze-image`,
  'embodied-reasoning': `${BACKEND_URL}/v1/vision/embodied-reasoning`,
  capabilities: `${BACKEND_URL}/v1/vision/capabilities`,
};

export async function POST(request: Request) {
  try {
    const url = new URL(request.url);
    const key = url.searchParams.get('endpoint') || 'reason';
    const targetUrl = ENDPOINT_URLS[key];

    if (!targetUrl) {
      return NextResponse.json({ error: 'Invalid endpoint' }, { status: 400 });
    }

    const formData = await request.formData();

    const response = await fetch(targetUrl, {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Vision service unavailable' }, { status: 503 });
  }
}

export async function GET() {
  try {
    const response = await fetch(ENDPOINT_URLS['capabilities']!);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Vision service unavailable' }, { status: 503 });
  }
}
