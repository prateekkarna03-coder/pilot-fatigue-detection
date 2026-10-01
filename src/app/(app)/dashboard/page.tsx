import type { Metadata } from "next";
import { TopBar } from "@/components/layout/top-bar";
import { SummaryCard } from "@/components/dashboard/summary-card";
import { RecentSessionsCard } from "@/components/dashboard/recent-sessions-table";
import {
  DASHBOARD_SUMMARY,
  RECENT_SESSIONS,
} from "@/data/placeholder";

export const metadata: Metadata = { title: "Dashboard" };

export default function DashboardPage() {
  return (
    <>
      <TopBar
        title="Dashboard"
        subtitle="Overview of active monitoring sessions and pilot safety status"
      />

      <main className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Summary cards */}
        <section
          className="grid grid-cols-2 gap-4 lg:grid-cols-4"
          aria-label="Summary statistics"
        >
          <SummaryCard
            label="Active Sessions"
            value={DASHBOARD_SUMMARY.activeSessions}
            description="Pilots currently monitored"
            accent="info"
          />
          <SummaryCard
            label="High Risk Pilots"
            value={DASHBOARD_SUMMARY.highRiskPilots}
            description="Requiring immediate review"
            accent="danger"
          />
          <SummaryCard
            label="Alerts Today"
            value={DASHBOARD_SUMMARY.alertsToday}
            description="Fatigue threshold exceeded"
            accent="warning"
          />
          <SummaryCard
            label="Avg Fatigue Score"
            value={DASHBOARD_SUMMARY.avgFatigueScore}
            description="Across all active pilots"
          />
        </section>

        {/* Recent sessions table */}
        <section aria-label="Recent monitoring sessions">
          <RecentSessionsCard sessions={RECENT_SESSIONS} />
        </section>
      </main>
    </>
  );
}
