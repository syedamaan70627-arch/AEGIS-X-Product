"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ROUTES } from "@/lib/routes";

export default function AnalysisRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace(ROUTES.reliability);
  }, [router]);

  return (
    <div className="p-8 text-center text-xs text-slate-400 font-mono">
      Redirecting to Reliability Assessment...
    </div>
  );
}
