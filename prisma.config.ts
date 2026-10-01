import "dotenv/config";
import { defineConfig, env } from "prisma/config";

export default defineConfig({
  // Path to the Prisma schema file
  schema: "prisma/schema.prisma",
  // Migration output directory and (optional) seed script
  migrations: {
    path: "prisma/migrations",
  },
  // Database connection — sourced from DATABASE_URL in .env
  datasource: {
    url: env("DATABASE_URL"),
  },
});
