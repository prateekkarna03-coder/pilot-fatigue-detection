export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';

export function classifyRisk(fatigueScore: number, kss: number): RiskLevel {
  if (fatigueScore > 80 || kss >= 8) return 'CRITICAL';
  if (fatigueScore > 65 || kss >= 7) return 'HIGH';
  if (fatigueScore > 40 || kss >= 5) return 'MODERATE';
  return 'LOW';
}
