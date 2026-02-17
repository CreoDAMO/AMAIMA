import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const ENDPOINT_URLS: Record<string, string> = {
  query: `${BACKEND_URL}/v1/biology/query`,
  discover: `${BACKEND_URL}/v1/biology/discover`,
  protein: `${BACKEND_URL}/v1/biology/protein`,
  optimize: `${BACKEND_URL}/v1/biology/optimize`,
};

export async function POST(request: Request) {
  try {
    const url = new URL(request.url);
    const key = url.searchParams.get('endpoint') || 'query';
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
