import type { HTMLAttributes, Ref } from "react";
import { cn } from "@/lib/utils";

type SkeletonProps = HTMLAttributes<HTMLDivElement> & {
  ref?: Ref<HTMLDivElement>;
};

export function Skeleton({ className, ref, ...props }: SkeletonProps) {
  return <div ref={ref} className={cn("animate-pulse rounded-lg bg-muted", className)} {...props} />;
}
