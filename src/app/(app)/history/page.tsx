import type { Metadata } from "next";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { RecentSessionsTable } from "@/components/dashboard/recent-sessions-table";
import { ALL_SESSIONS } from "@/data/placeholder";

export const metadata: Metadata = { title: "Session History" };

export default function HistoryPage() {
  return (
    <>
      <TopBar
        title="Session History"
        subtitle="Complete log of all pilot monitoring sessions"
        actions={
          <Button variant="outline" size="sm">
            Export CSV
          </Button>
        }
      />

      <main className="flex-1 overflow-y-auto p-6">
        <div className="rounded-lg border border-[#e2e8f0] bg-white shadow-sm">
          {/* Table header bar */}
          <div className="flex items-center justify-between border-b border-[#e2e8f0] px-5 py-3.5">
            <h2 className="text-sm font-semibold text-[#1e2d4a]">
              All Sessions
              <span className="ml-2 text-xs font-normal text-[#94a3b8]">
                ({ALL_SESSIONS.length} records)
              </span>
            </h2>
          </div>

          <RecentSessionsTable sessions={ALL_SESSIONS} />
        </div>
      </main>
    </>
  );
}
