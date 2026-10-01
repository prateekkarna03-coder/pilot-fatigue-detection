"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Eye,
  ClipboardList,
  FileText,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Monitoring", href: "/monitoring", icon: Eye },
  { label: "History", href: "/history", icon: ClipboardList },
  { label: "Reports", href: "/reports", icon: FileText },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-[#e2e8f0] bg-white">
      {/* Logo / Brand */}
      <div className="flex h-14 items-center gap-2.5 border-b border-[#e2e8f0] px-5">
        <ShieldCheck className="h-5 w-5 text-[#1e2d4a]" />
        <div className="flex flex-col leading-tight">
          <span className="text-xs font-bold text-[#1e2d4a] tracking-wide">PILOT SAFETY</span>
          <span className="text-[10px] text-[#94a3b8] uppercase tracking-widest">Fatigue Monitor</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-0.5 p-3 flex-1">
        {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-[#1e2d4a] text-white"
                  : "text-[#475569] hover:bg-[#f1f5f9] hover:text-[#1e2d4a]"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-[#e2e8f0] p-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#1e2d4a] text-white text-xs font-semibold">
            OP
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-xs font-medium text-[#1e2d4a]">Ops Controller</span>
            <span className="text-[10px] text-[#94a3b8]">ops@aviation.sys</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
