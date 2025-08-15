import { NextResponse } from 'next/server';
import resumeData from '@/data/resume.json';

export async function GET() {
  try {
    // Add cache headers for performance
    const headers = {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
    };

    return NextResponse.json(resumeData, { headers });
  } catch (error) {
    console.error('Error serving resume data:', error);
    return NextResponse.json(
      { error: 'Failed to load resume data' },
      { status: 500 }
    );
  }
}

export async function HEAD() {
  // Support HEAD requests for the API
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
    },
  });
}
