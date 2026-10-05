import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

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

    // 1. Resolve Pilot from User's email
    const pilot = await prisma.pilot.findUnique({
      where: { email },
    });

    if (!pilot) {
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
      return NextResponse.json(
        { 
          success: false, 
          error: "An active monitoring session already exists for this pilot." 
        },
        { status: 409 }
      );
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

    return NextResponse.json(
      { success: true, sessionId: newSession.id },
      { status: 201 }
    );
  } catch (error) {
    // Blanket catch-all, avoid leaking Prisma schema info
    console.error("Error creating monitoring session:", error);
    return NextResponse.json(
      { success: false, error: "An unexpected database error occurred." },
      { status: 500 }
    );
  }
}
