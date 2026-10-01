-- CreateEnum
CREATE TYPE "UserRole" AS ENUM ('ADMIN', 'OPERATIONS_CONTROLLER', 'ANALYST');

-- CreateEnum
CREATE TYPE "RiskLevel" AS ENUM ('LOW', 'MODERATE', 'HIGH', 'CRITICAL');

-- CreateEnum
CREATE TYPE "SessionStatus" AS ENUM ('ACTIVE', 'COMPLETED', 'FLAGGED', 'ABORTED');

-- CreateEnum
CREATE TYPE "RecommendationType" AS ENUM ('REST_BREAK', 'CREW_CHANGE', 'ALERT_CREW', 'MONITOR_CLOSELY', 'NOTIFY_GROUND');

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "role" "UserRole" NOT NULL DEFAULT 'OPERATIONS_CONTROLLER',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "pilots" (
    "id" TEXT NOT NULL,
    "employee_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "license_number" TEXT NOT NULL,
    "email" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "pilots_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "flights" (
    "id" TEXT NOT NULL,
    "flight_code" TEXT NOT NULL,
    "origin" TEXT NOT NULL,
    "destination" TEXT NOT NULL,
    "scheduled_at" TIMESTAMP(3) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "pilot_id" TEXT NOT NULL,

    CONSTRAINT "flights_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "monitoring_sessions" (
    "id" TEXT NOT NULL,
    "status" "SessionStatus" NOT NULL DEFAULT 'ACTIVE',
    "started_at" TIMESTAMP(3) NOT NULL,
    "ended_at" TIMESTAMP(3),
    "alert_count" INTEGER NOT NULL DEFAULT 0,
    "notes" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "pilot_id" TEXT NOT NULL,
    "flight_id" TEXT NOT NULL,

    CONSTRAINT "monitoring_sessions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "fatigue_measurements" (
    "id" TEXT NOT NULL,
    "captured_at" TIMESTAMP(3) NOT NULL,
    "fatigue_score" DOUBLE PRECISION NOT NULL,
    "eye_closure_percent" DOUBLE PRECISION NOT NULL,
    "blink_rate_per_min" DOUBLE PRECISION NOT NULL,
    "yawn_count" INTEGER NOT NULL,
    "head_pose_yaw" DOUBLE PRECISION NOT NULL,
    "head_pose_pitch" DOUBLE PRECISION NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "session_id" TEXT NOT NULL,

    CONSTRAINT "fatigue_measurements_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "risk_history" (
    "id" TEXT NOT NULL,
    "risk_level" "RiskLevel" NOT NULL,
    "fatigue_score" DOUBLE PRECISION NOT NULL,
    "triggered_at" TIMESTAMP(3) NOT NULL,
    "resolved_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "session_id" TEXT NOT NULL,

    CONSTRAINT "risk_history_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "recommendations" (
    "id" TEXT NOT NULL,
    "type" "RecommendationType" NOT NULL,
    "severity" "RiskLevel" NOT NULL,
    "message" TEXT NOT NULL,
    "issued_at" TIMESTAMP(3) NOT NULL,
    "acknowledged_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "session_id" TEXT NOT NULL,

    CONSTRAINT "recommendations_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "pilots_employee_id_key" ON "pilots"("employee_id");

-- CreateIndex
CREATE UNIQUE INDEX "pilots_license_number_key" ON "pilots"("license_number");

-- CreateIndex
CREATE UNIQUE INDEX "pilots_email_key" ON "pilots"("email");

-- CreateIndex
CREATE INDEX "pilots_employee_id_idx" ON "pilots"("employee_id");

-- CreateIndex
CREATE UNIQUE INDEX "flights_flight_code_key" ON "flights"("flight_code");

-- CreateIndex
CREATE INDEX "flights_pilot_id_idx" ON "flights"("pilot_id");

-- CreateIndex
CREATE INDEX "flights_scheduled_at_idx" ON "flights"("scheduled_at");

-- CreateIndex
CREATE INDEX "monitoring_sessions_pilot_id_idx" ON "monitoring_sessions"("pilot_id");

-- CreateIndex
CREATE INDEX "monitoring_sessions_flight_id_idx" ON "monitoring_sessions"("flight_id");

-- CreateIndex
CREATE INDEX "monitoring_sessions_started_at_idx" ON "monitoring_sessions"("started_at");

-- CreateIndex
CREATE INDEX "monitoring_sessions_status_idx" ON "monitoring_sessions"("status");

-- CreateIndex
CREATE INDEX "fatigue_measurements_session_id_idx" ON "fatigue_measurements"("session_id");

-- CreateIndex
CREATE INDEX "fatigue_measurements_captured_at_idx" ON "fatigue_measurements"("captured_at");

-- CreateIndex
CREATE INDEX "fatigue_measurements_session_id_captured_at_idx" ON "fatigue_measurements"("session_id", "captured_at");

-- CreateIndex
CREATE INDEX "risk_history_session_id_idx" ON "risk_history"("session_id");

-- CreateIndex
CREATE INDEX "risk_history_triggered_at_idx" ON "risk_history"("triggered_at");

-- CreateIndex
CREATE INDEX "risk_history_risk_level_idx" ON "risk_history"("risk_level");

-- CreateIndex
CREATE INDEX "recommendations_session_id_idx" ON "recommendations"("session_id");

-- CreateIndex
CREATE INDEX "recommendations_issued_at_idx" ON "recommendations"("issued_at");

-- CreateIndex
CREATE INDEX "recommendations_severity_idx" ON "recommendations"("severity");

-- AddForeignKey
ALTER TABLE "flights" ADD CONSTRAINT "flights_pilot_id_fkey" FOREIGN KEY ("pilot_id") REFERENCES "pilots"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "monitoring_sessions" ADD CONSTRAINT "monitoring_sessions_pilot_id_fkey" FOREIGN KEY ("pilot_id") REFERENCES "pilots"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "monitoring_sessions" ADD CONSTRAINT "monitoring_sessions_flight_id_fkey" FOREIGN KEY ("flight_id") REFERENCES "flights"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "fatigue_measurements" ADD CONSTRAINT "fatigue_measurements_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "monitoring_sessions"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "risk_history" ADD CONSTRAINT "risk_history_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "monitoring_sessions"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "recommendations" ADD CONSTRAINT "recommendations_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "monitoring_sessions"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
