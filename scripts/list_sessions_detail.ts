import dotenv from 'dotenv';
dotenv.config();
import { prisma } from '../src/lib/prisma';

async function main() {
  const sessions = await prisma.monitoringSession.findMany({
    orderBy: { startedAt: 'desc' },
    take: 5,
    include: {
      _count: {
        select: { measurements: true }
      }
    }
  });

  console.log('--- RECENT SESSIONS ---');
  for (const s of sessions) {
    console.log(`ID: ${s.id} | Status: ${s.status} | Started: ${s.startedAt.toISOString()} | Measurements: ${s._count.measurements}`);
  }
}

main().catch(console.error).finally(() => prisma.$disconnect());
