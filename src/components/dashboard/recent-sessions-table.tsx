import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { RiskBadge } from "@/components/ui/badges";
import { SessionStatusBadge } from "@/components/ui/badges";
import type { MonitoringSession } from "@/types";

interface RecentSessionsTableProps {
  sessions: MonitoringSession[];
}

export function RecentSessionsTable({ sessions }: RecentSessionsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Session ID</TableHead>
          <TableHead>Pilot</TableHead>
          <TableHead>Flight</TableHead>
          <TableHead>Date</TableHead>
          <TableHead>Duration</TableHead>
          <TableHead>Avg Score</TableHead>
          <TableHead>Peak Risk</TableHead>
          <TableHead>Alerts</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sessions.map((session) => (
          <TableRow key={session.id}>
            <TableCell className="font-mono text-xs text-[#94a3b8]">
              {session.id}
            </TableCell>
            <TableCell className="font-medium whitespace-nowrap">
              {session.pilotName}
            </TableCell>
            <TableCell className="font-mono text-xs">{session.flightId}</TableCell>
            <TableCell className="text-xs text-[#64748b]">{session.date}</TableCell>
            <TableCell className="text-xs">{session.duration}</TableCell>
            <TableCell>
              <span className="font-semibold tabular-nums">{session.avgFatigueScore}</span>
              <span className="text-[#94a3b8] text-xs">/100</span>
            </TableCell>
            <TableCell>
              <RiskBadge level={session.peakRiskLevel} />
            </TableCell>
            <TableCell className="text-center tabular-nums text-xs">
              {session.alertsCount}
            </TableCell>
            <TableCell>
              <SessionStatusBadge status={session.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

// Standalone variant with a "View All" link footer — for dashboard usage
export function RecentSessionsCard({ sessions }: RecentSessionsTableProps) {
  return (
    <div className="rounded-lg border border-[#e2e8f0] bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-[#e2e8f0] px-5 py-3.5">
        <h2 className="text-sm font-semibold text-[#1e2d4a]">Recent Monitoring Sessions</h2>
        <Link
          href="/history"
          className="text-xs font-medium text-[#1e2d4a] hover:underline"
        >
          View all →
        </Link>
      </div>
      <RecentSessionsTable sessions={sessions} />
    </div>
  );
}
