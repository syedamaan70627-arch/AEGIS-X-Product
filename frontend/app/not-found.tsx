import React from "react";
import Link from "next/link";
import { ShieldAlert, ArrowLeft, Home } from "lucide-react";
import { ROUTES } from "@/lib/routes";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-[#0F141B] flex flex-col items-center justify-center p-6 text-slate-200">
      <div className="max-w-md w-full p-8 rounded-2xl bg-[#151B23] border border-[#26303D] shadow-2xl text-center space-y-6">
        <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto">
          <ShieldAlert className="w-6 h-6" />
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-bold font-sans text-white">404 — Page Not Found</h1>
          <p className="text-xs text-slate-400 leading-relaxed font-sans">
            The requested AEGIS-X module or resource path does not exist or has been moved.
          </p>
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href={ROUTES.dashboard}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition"
          >
            <Home className="w-4 h-4" /> Command Center
          </Link>
          <Link
            href={ROUTES.reports}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition"
          >
            <ArrowLeft className="w-4 h-4" /> Integrated Reports
          </Link>
        </div>
      </div>
    </div>
  );
}
