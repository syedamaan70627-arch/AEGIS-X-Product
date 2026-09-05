"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { LoadingState } from "@/components/ui/LoadingState";

const PUBLIC_ROUTES = ["/login", "/signup", "/auth/confirm", "/auth/callback"];

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { loading, authenticated } = useAuth();

  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

  useEffect(() => {
    if (!loading && !authenticated && !isPublicRoute) {
      const search = searchParams?.toString();
      const currentPath = search ? `${pathname}?${search}` : pathname;
      const nextUrl = `/login?next=${encodeURIComponent(currentPath)}`;
      router.replace(nextUrl);
    }
  }, [loading, authenticated, isPublicRoute, pathname, searchParams, router]);

  // Public routes (login/signup) always render children without auth guard blocks
  if (isPublicRoute) {
    return <>{children}</>;
  }

  // While Supabase session hydration is still in progress for protected routes
  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <LoadingState message="Authenticating session..." />
      </div>
    );
  }

  // When auth hydration completes and user is unauthenticated on protected route
  if (!authenticated) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <LoadingState message="Redirecting to login..." />
      </div>
    );
  }

  // Authenticated user on protected route
  return <>{children}</>;
};
