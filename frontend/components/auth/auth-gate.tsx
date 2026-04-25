"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useUser } from "@/lib/hooks/useUser";
import { Skeleton } from "@/components/ui/skeleton";

export function AuthGate({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: user, error, isLoading, isFetching } = useUser();
  const unauthorized = error instanceof ApiError && error.status === 401;

  useEffect(() => {
    if (!isLoading && (unauthorized || user === null)) {
      router.replace(`/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [isLoading, pathname, router, unauthorized, user]);

  if (isLoading || isFetching || unauthorized || user === null) {
    return (
      <div className="grid gap-4">
        <Skeleton className="h-10 w-56" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-28 w-full" />
      </div>
    );
  }

  return <>{children}</>;
}
