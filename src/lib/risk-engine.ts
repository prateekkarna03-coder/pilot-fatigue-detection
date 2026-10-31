import { prisma } from '@/lib/prisma';
import { RiskLevel } from '@/generated/prisma/enums';
import { generateRecommendation } from './gemini';
import { classifyRisk } from './risk-level';

const sessionEvaluationQueues = new Map<string, Promise<void>>();
const recommendationAttempts = new Map<string, number>();
const RECOMMENDATION_COOLDOWN_MS = 5 * 60 * 1000;

interface TelemetryPayload {
  fatigueScore: number;
  eyeClosurePercent: number;
  blinkRatePerMin: number;
  yawnCount: number;
  headPoseDeviation: number;
  kss: number;
}

function canRequestRecommendation(sessionId: string) {
  const lastAttempt = recommendationAttempts.get(sessionId);
  if (lastAttempt && Date.now() - lastAttempt < RECOMMENDATION_COOLDOWN_MS) {
    return false;
  }

  recommendationAttempts.set(sessionId, Date.now());
  return true;
}

async function evaluateRisk(payload: TelemetryPayload, sessionId: string) {
  await prisma.fatigueMeasurement.create({
    data: {
      sessionId,
      fatigueScore: payload.fatigueScore,
      eyeClosurePercent: payload.eyeClosurePercent,
      blinkRatePerMin: payload.blinkRatePerMin,
      yawnCount: payload.yawnCount,
      headPoseYaw: payload.headPoseDeviation,
      headPosePitch: payload.headPoseDeviation,
      capturedAt: new Date()
    }
  });

  const newRiskLevel: RiskLevel = classifyRisk(payload.fatigueScore, payload.kss);

  const session = await prisma.monitoringSession.findUnique({
    where: { id: sessionId },
    include: {
      riskHistory: {
        orderBy: { triggeredAt: 'desc' },
        take: 1
      }
    }
  });

  const currentRisk = session?.riskHistory?.[0]?.riskLevel || 'LOW';
  if (newRiskLevel === currentRisk) return;

  await prisma.riskHistory.create({
    data: {
      sessionId,
      riskLevel: newRiskLevel,
      fatigueScore: payload.fatigueScore,
      triggeredAt: new Date()
    }
  });

  if (
    ['HIGH', 'CRITICAL'].includes(newRiskLevel) &&
    canRequestRecommendation(sessionId)
  ) {
    console.log("[RiskEngine] Requesting Gemini recommendation.", {
      sessionId,
      riskLevel: newRiskLevel,
    });
    await generateRecommendation(sessionId, {
      fatigueScore: payload.fatigueScore,
      blinkRate: payload.blinkRatePerMin,
      kss: payload.kss
    }, newRiskLevel);
  }
}

export function evaluateRiskAndPersist(payload: TelemetryPayload, sessionId: string) {
  const previous = sessionEvaluationQueues.get(sessionId) ?? Promise.resolve();
  const current = previous
    .catch(() => undefined)
    .then(() => evaluateRisk(payload, sessionId))
    .catch((error) => {
      console.error("Risk evaluation failed:", { sessionId, error });
    });

  sessionEvaluationQueues.set(sessionId, current);
  return current.finally(() => {
    if (sessionEvaluationQueues.get(sessionId) === current) {
      sessionEvaluationQueues.delete(sessionId);
    }
  });
}
