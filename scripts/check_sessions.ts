import "dotenv/config";
import { prisma } from "../src/lib/prisma";

async function main() {
  const sessions = await prisma.monitoringSession.findMany({
    orderBy: { startedAt: "desc" },
    take: 10,
    select: {
      id: true,
      pilotId: true,
      status: true,
      startedAt: true,
      endedAt: true,
      _count: { select: { measurements: true, recommendations: true } }
    }
  });
  for (const s of sessions) {
    if (s.status === 'ACTIVE') {
      console.log('ACTIVE_SESSION_ID:', s.id);
    }
  }
}

main().finally(() => prisma.$disconnect());
