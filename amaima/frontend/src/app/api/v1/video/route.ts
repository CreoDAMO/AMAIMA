import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const API_SECRET_KEY = process.env.API_SECRET_KEY || 'default_secret_key_for_development';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { searchParams } = new URL(request.url);
    const endpoint = searchParams.get('endpoint') || 'generate';
    
    const clientApiKey = request.headers.get('x-api-key') || '';
    
    const response = await fetch(`${BACKEND_URL}/v1/video/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': clientApiKey || API_SECRET_KEY,
      },
      body: JSON.stringify(body),
    });
    
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 503 });
  }
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const endpoint = searchParams.get('endpoint') || 'capabilities';
    
    const response = await fetch(`${BACKEND_URL}/v1/video/${endpoint}`, {
      method: 'GET',
    });
    
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 503 });
  }
}
