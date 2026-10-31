import { NextRequest, NextResponse } from 'next/server';
import { evaluateRiskAndPersist } from '@/lib/risk-engine';
import { prisma } from '@/lib/prisma';

export async function POST(req: NextRequest) {
  try {
    if (req.headers.get('x-telemetry-token') !== process.env.NEXTAUTH_SECRET) {
      return NextResponse.json({ success: false, error: 'Unauthorized telemetry source.' }, { status: 401 });
    }
    const payload = await req.json();

    if (typeof payload.sessionId !== 'string' || payload.sessionId.length === 0) {
      return NextResponse.json({ success: false, error: 'Telemetry sessionId is required.' }, { status: 400 });
    }

    const activeSession = await prisma.monitoringSession.findFirst({
      where: { id: payload.sessionId, status: 'ACTIVE' }
    });

    if (activeSession) {
      await evaluateRiskAndPersist(payload, activeSession.id);
      console.log(`[TelemetryAPI] Persisted telemetry for session ${activeSession.id}.`);
    } else {
      console.warn(`[TelemetryAPI] Ignored telemetry for inactive or unknown session ${payload.sessionId}.`);
    }

    return NextResponse.json({ success: Boolean(activeSession) });
  } catch (e) {
    console.error("Telemetry API failed", e);
    return NextResponse.json({ success: false }, { status: 500 });
  }
}
