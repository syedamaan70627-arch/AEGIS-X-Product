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
  X,
} from "lucide-react";

export const navigation = [
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

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen = true, onClose }) => {
  const pathname = usePathname();

  const content = (
    <aside className="w-64 bg-[#11161D] border-r border-[#26303D] flex flex-col shrink-0 h-screen sticky top-0 z-40 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-[#26303D] flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-[#3B82F6] flex items-center justify-center shadow-sm">
            <ShieldCheck className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-[#F3F4F6] tracking-wider font-sans">AEGIS-X</h1>
            <p className="text-[9px] uppercase font-sans font-semibold text-[#9CA3AF] tracking-widest">Enterprise Reliability</p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="md:hidden text-[#9CA3AF] hover:text-[#F3F4F6] p-1.5 rounded-lg hover:bg-[#1A222C] transition-colors"
            aria-label="Close Navigation Menu"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {navigation.map((group) => (
          <div key={group.group}>
            <h2 className="px-3 text-[10px] font-sans font-semibold text-[#6B7280] tracking-widest uppercase mb-1.5">
              {group.group}
            </h2>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => onClose?.()}
                    className={`flex items-center space-x-3 px-3 py-2 text-xs rounded-lg transition-all font-sans group ${
                      isActive
                        ? "bg-[#1A222C] text-[#F3F4F6] border-l-2 border-[#3B82F6] font-semibold"
                        : "text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-[#1A222C]/60 font-medium"
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 transition-colors ${isActive ? "text-[#3B82F6]" : "text-[#6B7280] group-hover:text-[#9CA3AF]"}`} />
                    <span className="truncate">{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-[#26303D] bg-[#11161D]">
        <div className="text-[11px] font-sans text-[#9CA3AF] flex items-center justify-between">
          <span>Engine Status:</span>
          <span className="text-[#22C55E] font-semibold flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]" />
            OPERATIONAL
          </span>
        </div>
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden md:block shrink-0">{content}</div>

      {/* Mobile Drawer Overlay */}
      {isOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-slate-950/80" onClick={onClose} />
          <div className="relative z-50 flex-1 max-w-xs w-full bg-slate-950">{content}</div>
        </div>
      )}
    </>
  );
};

