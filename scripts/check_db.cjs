const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

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
  console.log('--- DB SESSIONS ---');
  for (const s of sessions) {
    console.log(`SESSION: id=${s.id} status=${s.status} count=${s._count.measurements} started=${s.startedAt.toISOString()} ended=${s.endedAt?.toISOString() || 'NONE'}`);
  }
}

main().catch(console.error).finally(() => prisma.$disconnect());
