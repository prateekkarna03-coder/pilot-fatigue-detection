import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface SummaryCardProps {
  label: string;
  value: string | number;
  description?: string;
  accent?: "default" | "warning" | "danger" | "info";
}

const ACCENT_CLASSES: Record<NonNullable<SummaryCardProps["accent"]>, string> = {
  default: "text-[#1e2d4a]",
  warning: "text-amber-600",
  danger: "text-red-600",
  info: "text-blue-600",
};

export function SummaryCard({ label, value, description, accent = "default" }: SummaryCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className={cn("text-3xl font-bold tabular-nums", ACCENT_CLASSES[accent])}>
          {value}
        </p>
        {description && (
          <p className="mt-1 text-xs text-[#94a3b8]">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}
