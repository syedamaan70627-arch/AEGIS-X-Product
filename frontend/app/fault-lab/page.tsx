"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ROUTES } from "@/lib/routes";

export default function FaultLabRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace(ROUTES.faultLab);
  }, [router]);

  return (
    <div className="p-8 text-center text-xs text-slate-400 font-mono">
      Redirecting to Fault Lab...
    </div>
  );
}
