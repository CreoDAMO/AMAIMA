import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const API_SECRET_KEY = process.env.API_SECRET_KEY || 'default_secret_key_for_development';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const authHeader = request.headers.get('Authorization') || '';
    const clientApiKey = request.headers.get('x-api-key') || '';
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-API-Key': clientApiKey || API_SECRET_KEY,
    };
    if (authHeader) headers['Authorization'] = authHeader;

    const response = await fetch(`${BACKEND_URL}/v1/query/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({ error: 'Stream failed' }));
      return NextResponse.json(data, { status: response.status });
    }

    const stream = response.body;
    if (!stream) {
      return NextResponse.json({ error: 'No stream body' }, { status: 500 });
    }

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 503 });
  }
}
