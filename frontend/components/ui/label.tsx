import type { LabelHTMLAttributes, Ref } from "react";
import { cn } from "@/lib/utils";

type LabelProps = LabelHTMLAttributes<HTMLLabelElement> & {
  ref?: Ref<HTMLLabelElement>;
};

export function Label({ className, ref, ...props }: LabelProps) {
  return <label ref={ref} className={cn("text-sm font-medium text-foreground", className)} {...props} />;
}
