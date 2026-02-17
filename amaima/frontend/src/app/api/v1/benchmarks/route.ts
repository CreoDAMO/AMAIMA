import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const model = searchParams.get('model');
  const days = searchParams.get('days');

  try {
    const url = new URL(`${BACKEND_URL}/v1/benchmarks`);
    if (model) url.searchParams.append('model', model);
    if (days) url.searchParams.append('days', days);

    const response = await fetch(url.toString(), {
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 503 });
  }
}
