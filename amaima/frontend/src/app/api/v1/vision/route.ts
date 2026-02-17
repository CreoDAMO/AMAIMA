import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const url = new URL(request.url);
    const endpoint = url.searchParams.get('endpoint') || 'reason';
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
