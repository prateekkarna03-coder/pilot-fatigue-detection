import { PrismaClient } from '@/generated/prisma/client';
import { PrismaPg } from '@prisma/adapter-pg';
import * as dotenv from 'dotenv';

// Load environment variables from .env
dotenv.config();

async function main() {
  if (process.env.NODE_ENV === 'production') {
    console.error('This seed script is strictly for local development and cannot be run in production.');
    process.exit(1);
  }

  const email = process.env.ADMIN_EMAIL;
  if (!email) {
    console.error('Please set ADMIN_EMAIL environment variable to map to the Pilot.');
    process.exit(1);
  }

  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) {
    console.error('DATABASE_URL environment variable is not set.');
    process.exit(1);
  }

  const adapter = new PrismaPg({ connectionString });
  const prisma = new PrismaClient({ adapter });

  try {
    const safeEmployeeId = 'EMP-DEV-001';
    const safeLicenseNumber = 'LIC-DEV-001';
    const safeFlightCode = 'DEV-FLIGHT-001';

    console.log(`Checking for existing pilot mapped to: ${email}...`);

    // 1. Create or ensure Pilot exists idempotently
    const pilot = await prisma.pilot.upsert({
      where: { email },
      update: {}, // Do nothing if it already exists
      create: {
        email,
        employeeId: safeEmployeeId,
        name: 'Development Pilot',
        licenseNumber: safeLicenseNumber,
      },
    });

    console.log(`Pilot ensured! ID: ${pilot.id}`);

    // 2. Create or ensure Flight exists idempotently assigned to this pilot
    console.log(`Ensuring flight ${safeFlightCode} exists for pilot...`);

    const flight = await prisma.flight.upsert({
      where: { flightCode: safeFlightCode },
      update: {
        pilotId: pilot.id, // Ensure it is still bound to this pilot
      },
      create: {
        flightCode: safeFlightCode,
        origin: 'JFK',
        destination: 'LAX',
        scheduledAt: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours from now
        pilotId: pilot.id,
      },
    });

    console.log(`Flight ensured! ID: ${flight.id}`);
    console.log('Seed completed successfully.');

  } catch (error) {
    console.error('Error seeding pilot and flight test data:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

main();
