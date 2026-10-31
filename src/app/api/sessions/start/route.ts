import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { isWorkerRunningForSession, startWorker } from "@/lib/worker-manager";

export async function POST(req: Request) {
  console.log("[SessionsAPI] Start request received.");
  try {
    const session = await getServerSession(authOptions);

    if (!session || !session.user || !session.user.email) {
      console.warn("[SessionsAPI] Start request rejected: unauthenticated.");
      return NextResponse.json(
        { success: false, error: "Unauthorized. Please log in first." },
        { status: 401 }
      );
    }

    const { email } = session.user;

    // 1. Resolve Pilot from User's email
    const pilot = await prisma.pilot.findUnique({
      where: { email },
    });

    if (!pilot) {
      console.warn("[SessionsAPI] Start request rejected: pilot not found.", { email });
      return NextResponse.json(
        { success: false, error: "Authenticated user is not registered as a pilot." },
        { status: 403 }
      );
    }

    // 2. Parse payload
    let body;
    try {
      body = await req.json();
    } catch {
      return NextResponse.json(
        { success: false, error: "Invalid JSON body format." },
        { status: 400 }
      );
    }

    const { flightId } = body;

    if (!flightId || typeof flightId !== "string" || flightId.trim() === "") {
      console.warn("[SessionsAPI] Start request rejected: invalid flightId.");
      return NextResponse.json(
        { success: false, error: "Valid 'flightId' is required." },
        { status: 400 }
      );
    }

    // 3. Validate Flight belongs to Pilot
    const flight = await prisma.flight.findFirst({
      where: { id: flightId, pilotId: pilot.id },
    });

    if (!flight) {
      console.warn("[SessionsAPI] Start request rejected: flight not found.", {
        flightId,
        pilotId: pilot.id,
      });
      return NextResponse.json(
        { success: false, error: "Flight not found or not assigned to this pilot." },
        { status: 404 }
      );
    }

    // 4. Ensure no conflicting ACTIVE session
    const existingActiveSession = await prisma.monitoringSession.findFirst({
      where: {
        pilotId: pilot.id,
        status: "ACTIVE",
      },
    });

    if (existingActiveSession) {
      if (
        !isWorkerRunningForSession(existingActiveSession.id) &&
        existingActiveSession.startedAt.getTime() < Date.now() - 60_000
      ) {
        console.warn("[SessionsAPI] Recovering stale active session before starting a new one.", {
          sessionId: existingActiveSession.id,
          pilotId: pilot.id,
        });
        await prisma.monitoringSession.update({
          where: { id: existingActiveSession.id },
          data: { status: "ABORTED", endedAt: new Date() },
        });
      } else {
        console.warn("[SessionsAPI] Start request rejected: active session exists.", {
          sessionId: existingActiveSession.id,
          pilotId: pilot.id,
        });
        return NextResponse.json(
          {
            success: false,
            error: "An active monitoring session already exists for this pilot."
          },
          { status: 409 }
        );
      }
    }

    // 5. Create real monitoring session
    const newSession = await prisma.monitoringSession.create({
      data: {
        pilotId: pilot.id,
        flightId: flight.id,
        status: "ACTIVE",
        startedAt: new Date(),
        alertCount: 0,
      },
    });
    console.log("[SessionsAPI] Monitoring session created.", {
      sessionId: newSession.id,
      pilotId: pilot.id,
      flightId: flight.id,
    });

    // 6. Hook Python Worker
    const workerStarted = await startWorker(newSession.id);
    if (!workerStarted) {
      console.error("[SessionsAPI] Python worker failed to start.", {
        sessionId: newSession.id,
      });
      // Rollback session defensively
      await prisma.monitoringSession.delete({ where: { id: newSession.id } });
      return NextResponse.json(
        { success: false, error: "Failed to initialize CV tracking pipeline. Webcam may be unavailable." },
        { status: 500 }
      );
    }

    console.log("[SessionsAPI] Monitoring session started.", {
      sessionId: newSession.id,
    });
    return NextResponse.json(
      { success: true, sessionId: newSession.id },
      { status: 201 }
    );
  } catch (error) {
    // Blanket catch-all, avoid leaking Prisma schema info
    console.error("[SessionsAPI] Error creating monitoring session:", error);
    return NextResponse.json(
      { success: false, error: "An unexpected database error occurred." },
      { status: 500 }
    );
  }
}
