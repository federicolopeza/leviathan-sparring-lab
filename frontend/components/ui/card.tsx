import type { HTMLAttributes, Ref } from "react";
import { cn } from "@/lib/utils";

type DivProps = HTMLAttributes<HTMLDivElement> & {
  ref?: Ref<HTMLDivElement>;
};

export function Card({ className, ref, ...props }: DivProps) {
  return <div ref={ref} className={cn("rounded-2xl border border-border bg-card text-card-foreground shadow-sm", className)} {...props} />;
}

export function CardHeader({ className, ref, ...props }: DivProps) {
  return <div ref={ref} className={cn("grid gap-1.5 p-6", className)} {...props} />;
}

export function CardContent({ className, ref, ...props }: DivProps) {
  return <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />;
}

export function CardFooter({ className, ref, ...props }: DivProps) {
  return <div ref={ref} className={cn("flex items-center gap-3 p-6 pt-0", className)} {...props} />;
}
