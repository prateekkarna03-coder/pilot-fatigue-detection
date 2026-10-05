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
  const router = useRouter();

  const handleStopSession = async () => {
    if (!sessionId) return;

    setIsLoading(true);

    try {
      const response = await fetch("/api/sessions/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId }),
      });

      if (!response.ok) {
        console.error("Failed to stop session:", await response.json());
        setIsLoading(false);
        return;
      }

      // Success: Redirect back to the dashboard to allow starting a new session
      router.push("/dashboard");
    } catch (err) {
      console.error(err);
      setIsLoading(false);
    }
  };

  return (
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
  );
}
