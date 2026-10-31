import { GoogleGenAI } from '@google/genai';
import { prisma } from '@/lib/prisma';
import { RiskLevel, RecommendationType } from '@/generated/prisma/enums';

const GEMINI_MODEL = 'gemini-3.8-flash';

export type GeminiStatus = 'ready' | 'missing-key' | 'request-failed';

let lastStatus: GeminiStatus = process.env.GEMINI_API_KEY?.trim()
  ? 'ready'
  : 'missing-key';

export function getGeminiStatus(): GeminiStatus {
  return lastStatus;
}

export async function generateRecommendation(
  sessionId: string, 
  metrics: { fatigueScore: number, blinkRate: number, kss: number }, 
  riskLevel: RiskLevel
) {
  const apiKey = process.env.GEMINI_API_KEY?.trim();
  if (!apiKey) {
    lastStatus = 'missing-key';
    console.warn("[Gemini] GEMINI_API_KEY is not configured; recommendation skipped.");
    return;
  }

  const prompt = `
    You are an Aviation Fatigue Risk Engine.
    Pilot metrics: Fatigue Score ${metrics.fatigueScore}/100, KSS: ${metrics.kss}, Blink Rate: ${metrics.blinkRate}/min.
    Current assessed risk level: ${riskLevel}.
    Based on this, what is your recommendation? Reply only with short, actionable text.
  `;

  try {
    const ai = new GoogleGenAI({ apiKey });
    const response = await ai.models.generateContent({
      model: GEMINI_MODEL,
      contents: prompt,
    });

    const msg = response.text?.trim();
    if (!msg) {
      lastStatus = 'request-failed';
      console.error("[Gemini] Request returned no recommendation text.");
      return;
    }
    
    // Choose recommendation type based on risk
    let rType: RecommendationType = RecommendationType.MONITOR_CLOSELY;
    if (riskLevel === 'CRITICAL') rType = RecommendationType.ALERT_CREW;
    else if (riskLevel === 'HIGH') rType = RecommendationType.REST_BREAK;

    await prisma.recommendation.create({
      data: {
        sessionId,
        message: msg,
        severity: riskLevel,
        type: rType,
        issuedAt: new Date()
      }
    });
    lastStatus = 'ready';

  } catch (error) {
    lastStatus = 'request-failed';
    const apiError = error as {
      name?: string;
      status?: number;
      statusCode?: number;
      message?: string;
    };
    console.error("[Gemini] Recommendation request failed.", {
      model: GEMINI_MODEL,
      name: apiError.name ?? "UnknownError",
      status: apiError.status ?? apiError.statusCode ?? "unknown",
      message: (apiError.message ?? "No error message returned.").replaceAll(
        apiKey,
        "[REDACTED]"
      ),
    });
  }
}
