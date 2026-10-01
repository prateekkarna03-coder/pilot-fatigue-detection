import type { Metadata } from "next";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ReportStatusBadge } from "@/components/ui/badges";
import { REPORTS } from "@/data/placeholder";

export const metadata: Metadata = { title: "Reports" };

export default function ReportsPage() {
  return (
    <>
      <TopBar
        title="Reports"
        subtitle="Generated session summaries, incident reports, and weekly overviews"
        actions={
          <Button size="sm">Generate Report</Button>
        }
      />

      <main className="flex-1 overflow-y-auto p-6">
        <div className="rounded-lg border border-[#e2e8f0] bg-white shadow-sm">
          {/* Table header bar */}
          <div className="flex items-center justify-between border-b border-[#e2e8f0] px-5 py-3.5">
            <h2 className="text-sm font-semibold text-[#1e2d4a]">
              Report Archive
              <span className="ml-2 text-xs font-normal text-[#94a3b8]">
                ({REPORTS.length} reports)
              </span>
            </h2>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Report ID</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Pilot / Scope</TableHead>
                <TableHead>Period</TableHead>
                <TableHead>Generated</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Size</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {REPORTS.map((report) => (
                <TableRow key={report.id}>
                  <TableCell className="font-mono text-xs text-[#94a3b8]">
                    {report.id}
                  </TableCell>
                  <TableCell className="font-medium whitespace-nowrap text-sm">
                    {report.reportType}
                  </TableCell>
                  <TableCell className="text-sm text-[#475569] whitespace-nowrap">
                    {report.relatedPilot}
                  </TableCell>
                  <TableCell className="text-xs text-[#64748b] whitespace-nowrap">
                    {report.period}
                  </TableCell>
                  <TableCell className="text-xs text-[#64748b]">
                    {report.generatedDate}
                  </TableCell>
                  <TableCell>
                    <ReportStatusBadge status={report.status} />
                  </TableCell>
                  <TableCell className="text-xs tabular-nums text-[#94a3b8]">
                    {report.fileSizeKb > 0
                      ? `${report.fileSizeKb} KB`
                      : "—"}
                  </TableCell>
                  <TableCell>
                    {report.status === "Generated" && (
                      <Button variant="outline" size="sm">
                        Download
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </main>
    </>
  );
}
