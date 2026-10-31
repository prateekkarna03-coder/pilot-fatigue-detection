"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { PlayCircle, Loader2 } from "lucide-react";

interface Flight {
  id: string;
  flightCode: string;
  origin: string;
  destination: string;
}

interface StartMonitoringButtonProps {
  flights: Flight[];
}

export function StartMonitoringButton({ flights }: StartMonitoringButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFlightId, setSelectedFlightId] = useState<string>(flights[0]?.id || "");
  const router = useRouter();

  // Guard: if no flights, don't show the monitoring controls
  if (!flights || flights.length === 0) {
    return null;
  }

  const handleStartSession = async () => {
    if (!selectedFlightId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/sessions/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ flightId: selectedFlightId }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Failed to start session.");
        setIsLoading(false);
        return;
      }

      // Success: Navigate to monitoring and refresh server-rendered state
      router.push("/monitoring");
      router.refresh();
    } catch (err) {
      console.error(err);
      setError("A network error occurred.");
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-2">
        <select
          value={selectedFlightId}
          onChange={(e) => setSelectedFlightId(e.target.value)}
          disabled={isLoading}
          className="h-9 shrink-0 rounded-md border border-[#e2e8f0] bg-white px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950 disabled:cursor-not-allowed disabled:opacity-50 text-[#1e2d4a] font-medium"
        >
          {flights.map((f) => (
            <option key={f.id} value={f.id}>
              {f.flightCode} ({f.origin} → {f.destination})
            </option>
          ))}
        </select>
        <Button
          onClick={handleStartSession}
          disabled={isLoading || !selectedFlightId}
          className="bg-[#2463eb] hover:bg-[#1d4ed8] text-white whitespace-nowrap"
        >
          {isLoading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <PlayCircle className="mr-2 h-4 w-4" />
          )}
          {isLoading ? "Starting..." : "Start"}
        </Button>
      </div>
      {error && <span className="text-xs text-red-500 font-medium">{error}</span>}
    </div>
  );
}
