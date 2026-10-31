"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/badges";
import type { AiRecommendation } from "@/types";
import type { GeminiStatus } from "@/lib/gemini";

interface AiRecommendationsPanelProps {
  recommendations: AiRecommendation[];
  status: GeminiStatus;
  sessionId: string;
}

export function AiRecommendationsPanel({
  recommendations,
  status,
  sessionId,
}: AiRecommendationsPanelProps) {
  const [liveRecommendations, setLiveRecommendations] = useState(recommendations);
  const [liveStatus, setLiveStatus] = useState(status);

  useEffect(() => {
    let cancelled = false;
    const refresh = async () => {
      const response = await fetch(`/api/sessions/${sessionId}/recommendations`, {
        cache: "no-store",
      });
      if (!response.ok || cancelled) return;
      const data = await response.json();
      setLiveRecommendations(data.recommendations);
      setLiveStatus(data.status);
    };

    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [sessionId]);

  const statusMessage =
    liveStatus === "missing-key"
      ? "AI recommendations are unavailable because the server Gemini API key is not configured."
      : liveStatus === "request-failed"
        ? "AI recommendations are temporarily unavailable because the Gemini request failed. Check the server logs."
        : null;

  return (
    <Card>
      <CardHeader className="p-4 pb-2">
        <CardTitle>AI Recommendations</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 px-4 pb-3 pt-0">
        {statusMessage ? (
          <p className="text-xs leading-relaxed text-[#64748b]">
            {statusMessage}
          </p>
        ) : null}
        {liveRecommendations.length === 0 && !statusMessage ? (
          <p className="text-xs leading-relaxed text-[#64748b]">
            No AI recommendations have been generated for this session yet.
          </p>
        ) : (
          liveRecommendations.map((rec) => (
            <div
              key={rec.id}
              className="rounded border border-[#e2e8f0] bg-[#f8fafc] p-2"
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
          ))
        )}
      </CardContent>
    </Card>
  );
}
