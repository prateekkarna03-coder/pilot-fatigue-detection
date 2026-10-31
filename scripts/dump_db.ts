import fs from 'fs';
import { prisma } from '../src/lib/prisma';

async function main() {
  const sessions = await prisma.monitoringSession.findMany({
    orderBy: { startedAt: 'desc' },
    take: 10,
    select: {
      id: true,
      pilotId: true,
      status: true,
      startedAt: true,
      endedAt: true,
      _count: { select: { measurements: true } }
    }
  });

  const pilots = await prisma.pilot.findMany();
  const measurements = await prisma.fatigueMeasurement.findMany({
    orderBy: { capturedAt: 'desc' },
    take: 5
  });

  fs.writeFileSync('scripts/db_status.json', JSON.stringify({ sessions, pilots, measurements }, null, 2));
  console.log('Written to scripts/db_status.json');
}

main().finally(() => prisma.$disconnect());
