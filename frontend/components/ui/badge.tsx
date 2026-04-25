import type { HTMLAttributes, Ref } from "react";
import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  ref?: Ref<HTMLSpanElement>;
  variant?: BadgeVariant;
};

const variants: Record<BadgeVariant, string> = {
  default: "border-primary/30 bg-primary/10 text-primary",
  success: "border-accent/30 bg-accent/10 text-accent",
  warning: "border-[#D97706]/30 bg-[#D97706]/10 text-[#92400E]",
  destructive: "border-destructive/30 bg-destructive/10 text-destructive",
  muted: "border-border bg-muted text-muted-foreground"
};

export function Badge({ className, ref, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      ref={ref}
      className={cn("inline-flex h-7 items-center rounded-full border px-2.5 text-xs font-semibold", variants[variant], className)}
      {...props}
    />
  );
}
