"use client";

import React, { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { LoadingState } from "@/components/ui/LoadingState";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const search = searchParams?.toString();
    const target = search ? `/auth/confirm?${search}` : "/auth/confirm";
    router.replace(target);
  }, [router, searchParams]);

  return (
    <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center font-sans text-[#F3F4F6]">
      <LoadingState message="Redirecting to verification processor..." />
    </div>
  );
}
