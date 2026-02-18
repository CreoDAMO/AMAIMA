import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const authHeader = request.headers.get('Authorization') || '';
    const response = await fetch(`${BACKEND_URL}/v1/auth/me`, {
      headers: { 'Authorization': authHeader },
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 503 });
  }
}
