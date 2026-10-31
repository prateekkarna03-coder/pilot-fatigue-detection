import { prisma } from '../src/lib/prisma';

async function main() {
  const pilot = await prisma.pilot.findFirst();
  if (!pilot) throw new Error("No pilot found");
  const flight = await prisma.flight.findFirst({ where: { pilotId: pilot.id } });
  if (!flight) throw new Error("No flight found");

  // Deactivate any existing active sessions
  await prisma.monitoringSession.updateMany({
    where: { pilotId: pilot.id, status: 'ACTIVE' },
    data: { status: 'COMPLETED', endedAt: new Date() }
  });

  const session = await prisma.monitoringSession.create({
    data: {
      pilotId: pilot.id,
      flightId: flight.id,
      status: 'ACTIVE',
      startedAt: new Date(),
      alertCount: 0
    }
  });

  console.log("ACTIVE_SESSION_ID=" + session.id);
}

main().catch(console.error).finally(() => prisma.$disconnect());
