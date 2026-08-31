"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  AlertOctagon,
  BrainCircuit,
  Database,
  FileCheck,
  FileSpreadsheet,
  FileText,
  Layers,
  LineChart,
  ShieldCheck,
  Zap,
} from "lucide-react";

const navigation = [
  {
    group: "OVERVIEW",
    items: [
      { name: "Command Center", href: "/dashboard", icon: ShieldCheck },
    ],
  },
  {
    group: "OPERATIONS",
    items: [
      { name: "Models", href: "/models", icon: Layers },
      { name: "Data Setup", href: "/data", icon: Database },
      { name: "Batch Monitor", href: "/monitor", icon: Activity },
      { name: "Reliability", href: "/reliability", icon: LineChart },
    ],
  },
  {
    group: "TESTING",
    items: [
      { name: "Stress Lab", href: "/stress", icon: Zap },
      { name: "Fault Lab", href: "/faults", icon: AlertOctagon },
    ],
  },
  {
    group: "INTELLIGENCE",
    items: [
      { name: "Failure Explorer", href: "/failures", icon: FileSpreadsheet },
      { name: "Failure Memory", href: "/memory", icon: BrainCircuit },
      { name: "Failure Prediction", href: "/prediction", icon: FileCheck },
      { name: "Early Warning", href: "/warnings", icon: Activity },
    ],
  },
  {
    group: "OUTPUT",
    items: [
      { name: "Reports", href: "/reports", icon: FileText },
    ],
  },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800/80 flex flex-col shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-950/50">
          <ShieldCheck className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-base font-bold text-slate-100 tracking-wider">AEGIS-X</h1>
          <p className="text-[10px] uppercase font-semibold text-slate-400 tracking-widest">Reliability Platform</p>
        </div>
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navigation.map((group) => (
          <div key={group.group}>
            <h2 className="px-3 text-[10px] font-bold text-slate-400 tracking-widest uppercase mb-2">
              {group.group}
            </h2>
            <div className="space-y-1">
              {group.items.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center space-x-3 px-3 py-2 text-xs font-medium rounded-lg transition-all ${
                      isActive
                        ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 font-semibold"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/50">
        <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between">
          <span>Engine Status:</span>
          <span className="text-emerald-400 font-semibold flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            OPERATIONAL
          </span>
        </div>
      </div>
    </aside>
  );
};
