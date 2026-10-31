import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { stopWorker } from "@/lib/worker-manager";

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions);

    if (!session || !session.user || !session.user.email) {
      return NextResponse.json(
        { success: false, error: "Unauthorized. Please log in first." },
        { status: 401 }
      );
    }

    const { email } = session.user;

    const pilot = await prisma.pilot.findUnique({
      where: { email },
    });

    if (!pilot) {
      return NextResponse.json(
        { success: false, error: "Authenticated user is not registered as a pilot." },
        { status: 403 }
      );
    }

    let body;
    try {
      body = await req.json();
    } catch {
      return NextResponse.json(
        { success: false, error: "Invalid JSON body format." },
        { status: 400 }
      );
    }

    const { sessionId } = body;

    if (!sessionId || typeof sessionId !== "string" || sessionId.trim() === "") {
      return NextResponse.json(
        { success: false, error: "Valid 'sessionId' is required." },
        { status: 400 }
      );
    }

    // Identify the session from the request, verifying ownership
    const monitoringSession = await prisma.monitoringSession.findFirst({
      where: { id: sessionId, pilotId: pilot.id },
    });

    if (!monitoringSession) {
      return NextResponse.json(
        { success: false, error: "Session not found or not owned by pilot." },
        { status: 404 }
      );
    }

    if (monitoringSession.status !== "ACTIVE") {
      return NextResponse.json({ success: true, alreadyStopped: true }, { status: 200 });
    }

    let workerStopped = false;
    try {
      workerStopped = await stopWorker(sessionId);
    } catch (error) {
      console.error("[SessionsAPI] Worker shutdown threw an error.", { sessionId, error });
    }
    const finalStatus = workerStopped ? "COMPLETED" : "ABORTED";
    const updated = await prisma.monitoringSession.updateMany({
      where: { id: sessionId, pilotId: pilot.id, status: "ACTIVE" },
      data: { status: finalStatus, endedAt: new Date() },
    });
    if (updated.count !== 1) {
      return NextResponse.json({ success: true, alreadyStopped: true }, { status: 200 });
    }

    if (!workerStopped) {
      console.error("[SessionsAPI] Worker shutdown failed; session marked ABORTED.", { sessionId });
      return NextResponse.json(
        { success: false, error: "The monitoring worker did not stop cleanly. The session was marked aborted." },
        { status: 500 }
      );
    }

    return NextResponse.json(
      { success: true },
      { status: 200 }
    );
  } catch (error) {
    console.error("Error stopping monitoring session:", error);
    return NextResponse.json(
      { success: false, error: "An unexpected database error occurred." },
      { status: 500 }
    );
  }
}
