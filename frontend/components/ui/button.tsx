import type { ButtonHTMLAttributes, Ref } from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost" | "destructive";
type ButtonSize = "sm" | "md" | "lg";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  ref?: Ref<HTMLButtonElement>;
  variant?: ButtonVariant;
  size?: ButtonSize;
};

const variants: Record<ButtonVariant, string> = {
  primary: "bg-primary text-white shadow-[0_12px_30px_rgba(110,86,207,0.24)] hover:bg-[#5f49bc]",
  secondary: "border border-border bg-card text-card-foreground hover:bg-muted",
  ghost: "text-muted-foreground hover:bg-muted hover:text-foreground",
  destructive: "bg-destructive text-white hover:bg-[#b42318]"
};

const sizes: Record<ButtonSize, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-11 px-4 text-sm",
  lg: "h-12 px-5 text-base"
};

export function Button({ className, variant = "primary", size = "md", ref, ...props }: ButtonProps) {
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition disabled:cursor-not-allowed disabled:opacity-55",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}
