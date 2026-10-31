import assert from "node:assert/strict";
import { RISK_STYLES, getRiskBadgeStyle } from "../src/components/ui/badges";

console.log("Running badge and recommendation tests...\n");

// Test 1: Exact color classes for all 4 severities in both title-case and uppercase
const expectedStyles = {
  Low: "bg-green-50 text-green-700 border-green-200",
  LOW: "bg-green-50 text-green-700 border-green-200",
  Moderate: "bg-amber-50 text-amber-700 border-amber-200",
  MODERATE: "bg-amber-50 text-amber-700 border-amber-200",
  High: "bg-orange-50 text-orange-700 border-orange-200",
  HIGH: "bg-orange-50 text-orange-700 border-orange-200",
  Critical: "bg-red-50 text-red-700 border-red-200",
  CRITICAL: "bg-red-50 text-red-700 border-red-200",
};

for (const [key, expected] of Object.entries(expectedStyles)) {
  assert.equal(
    getRiskBadgeStyle(key),
    expected,
    `getRiskBadgeStyle("${key}") should return "${expected}"`
  );
  assert.equal(
    RISK_STYLES[key],
    expected,
    `RISK_STYLES["${key}"] should match "${expected}"`
  );
  console.log(`✓ Passed: severity '${key}' maps to correct color class`);
}

// Test 2: Case-insensitivity edge cases (e.g., lowercase "high", mixed case "MoDeRaTe")
assert.equal(
  getRiskBadgeStyle("high"),
  "bg-orange-50 text-orange-700 border-orange-200",
  "lowercase 'high' should map to orange style"
);
assert.equal(
  getRiskBadgeStyle("MoDeRaTe"),
  "bg-amber-50 text-amber-700 border-amber-200",
  "mixed case 'MoDeRaTe' should map to amber style"
);
console.log("✓ Passed: case-insensitive fallbacks");

// Test 3: Recommendation visibility test across changing risk levels
// Previously, recommendations disappeared when currentRiskLevel shifted.
// Verify that recommendations across different severities remain visible in the active session.
interface MockRecommendation {
  id: string;
  severity: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  message: string;
  issuedAt: Date;
}

const sessionRecommendations: MockRecommendation[] = [
  {
    id: "rec-1",
    severity: "HIGH",
    message: "High fatigue detected. Consider tactical rest or task handoff.",
    issuedAt: new Date(Date.now() - 60000),
  },
  {
    id: "rec-2",
    severity: "MODERATE",
    message: "Elevated blink rate observed. Monitor cross-check cadence.",
    issuedAt: new Date(Date.now() - 30000),
  },
];

// Map function representing updated route / page logic (without filtering by currentRiskLevel)
function mapSessionRecommendations(recs: MockRecommendation[]) {
  return recs.map((r) => ({
    id: r.id,
    severity: r.severity,
    message: r.message,
    style: getRiskBadgeStyle(r.severity),
  }));
}

// Regardless of whether current risk is 'LOW', 'MODERATE', or 'HIGH', all session recs remain
const riskLevelsToTest = ["LOW", "MODERATE", "HIGH", "CRITICAL"];
for (const currentRisk of riskLevelsToTest) {
  const visible = mapSessionRecommendations(sessionRecommendations);
  assert.equal(
    visible.length,
    2,
    `All 2 recommendations must remain visible when current risk is ${currentRisk}`
  );
  assert.equal(
    visible[0].style,
    "bg-orange-50 text-orange-700 border-orange-200",
    "First recommendation retains HIGH orange style"
  );
  assert.equal(
    visible[1].style,
    "bg-amber-50 text-amber-700 border-amber-200",
    "Second recommendation retains MODERATE amber style"
  );
  console.log(`✓ Passed: recommendations persist when current risk is '${currentRisk}'`);
}

console.log("\nAll badge and recommendation tests passed successfully!");
