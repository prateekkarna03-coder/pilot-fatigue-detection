import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/badges";
import type { AiRecommendation } from "@/types";

interface AiRecommendationsPanelProps {
  recommendations: AiRecommendation[];
}

export function AiRecommendationsPanel({
  recommendations,
}: AiRecommendationsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Recommendations</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 pt-0">
        {recommendations.map((rec) => (
          <div
            key={rec.id}
            className="rounded border border-[#e2e8f0] bg-[#f8fafc] p-3"
          >
            <div className="flex items-center justify-between mb-1.5">
              <RiskBadge level={rec.severity} />
              <span className="text-[10px] text-[#94a3b8] font-mono">
                {rec.issuedAt}
              </span>
            </div>
            <p className="text-xs leading-relaxed text-[#475569]">
              {rec.message}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
