import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { getGeminiStatus } from "@/lib/gemini";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  const authSession = await getServerSession(authOptions);
  if (!authSession?.user?.email) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  const { sessionId } = await params;
  const pilot = await prisma.pilot.findUnique({
    where: { email: authSession.user.email },
    select: { id: true },
  });
  if (!pilot) {
    return NextResponse.json({ error: "Pilot not found." }, { status: 403 });
  }

  const session = await prisma.monitoringSession.findFirst({
    where: { id: sessionId, pilotId: pilot.id },
    select: {
      recommendations: {
        orderBy: { issuedAt: "desc" },
        take: 3,
      },
    },
  });
  if (!session) {
    return NextResponse.json({ error: "Session not found." }, { status: 404 });
  }

  return NextResponse.json({
    recommendations: session.recommendations.map((recommendation) => ({
      id: recommendation.id,
      severity: recommendation.severity,
      message: recommendation.message,
      issuedAt: recommendation.issuedAt.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    })),
    status: getGeminiStatus(),
  });
}
