import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const ALLOWED_ENDPOINTS = ['plan', 'execute', 'status', 'capabilities'];

export async function POST(request: Request) {
  try {
    const url = new URL(request.url);
    let endpoint = url.searchParams.get('endpoint') || 'plan';
    if (!ALLOWED_ENDPOINTS.includes(endpoint)) {
      endpoint = 'plan';
    }
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/v1/robotics/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Robotics service unavailable' }, { status: 503 });
  }
}

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/v1/robotics/capabilities`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Robotics service unavailable' }, { status: 503 });
  }
}
