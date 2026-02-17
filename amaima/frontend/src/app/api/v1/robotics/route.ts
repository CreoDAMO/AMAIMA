import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const ENDPOINT_URLS: Record<string, string> = {
  plan: `${BACKEND_URL}/v1/robotics/plan`,
  execute: `${BACKEND_URL}/v1/robotics/execute`,
  status: `${BACKEND_URL}/v1/robotics/status`,
  capabilities: `${BACKEND_URL}/v1/robotics/capabilities`,
};

export async function POST(request: Request) {
  try {
    const url = new URL(request.url);
    const key = url.searchParams.get('endpoint') || 'plan';
    const targetUrl = ENDPOINT_URLS[key];

    if (!targetUrl) {
      return NextResponse.json({ error: 'Invalid endpoint' }, { status: 400 });
    }

    const body = await request.json();

    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Robotics service unavailable' }, { status: 503 });
  }
}

export async function GET() {
  try {
    const response = await fetch(ENDPOINT_URLS['capabilities']!);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Robotics service unavailable' }, { status: 503 });
  }
}
