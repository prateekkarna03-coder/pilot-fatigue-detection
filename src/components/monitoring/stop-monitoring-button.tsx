"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface StopMonitoringButtonProps {
  sessionId: string;
}

export function StopMonitoringButton({ sessionId }: StopMonitoringButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleStopSession = async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/sessions/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        const message = data?.error || "Failed to end the monitoring session.";
        console.error("Failed to stop session:", message);
        setError(message);
        setIsLoading(false);
        return;
      }

      // Success: Redirect back to the dashboard to allow starting a new session
      router.push("/dashboard");
    } catch (err) {
      console.error(err);
      setError("A network error occurred while ending the session.");
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        variant="outline"
        size="sm"
        onClick={handleStopSession}
        disabled={isLoading}
      >
        {isLoading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : null}
        {isLoading ? "Ending..." : "End Session"}
      </Button>
      {error && <span className="text-xs font-medium text-red-500">{error}</span>}
    </div>
  );
}
