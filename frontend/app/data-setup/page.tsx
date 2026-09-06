"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ROUTES } from "@/lib/routes";

export default function DataSetupRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace(ROUTES.dataSetup);
  }, [router]);

  return (
    <div className="p-8 text-center text-xs text-slate-400 font-mono">
      Redirecting to Data Setup...
    </div>
  );
}
