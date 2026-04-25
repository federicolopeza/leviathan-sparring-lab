import type { InputHTMLAttributes, Ref } from "react";
import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  ref?: Ref<HTMLInputElement>;
  label?: string;
  error?: string;
};

export function Input({ className, id, label, error, ref, ...props }: InputProps) {
  const inputId = id ?? props.name;
  const errorId = error && inputId ? `${inputId}-error` : undefined;

  return (
    <div className="grid gap-2">
      {label ? <Label htmlFor={inputId}>{label}</Label> : null}
      <input
        ref={ref}
        id={inputId}
        aria-invalid={Boolean(error)}
        aria-describedby={errorId}
        className={cn(
          "h-11 w-full rounded-lg border bg-card px-3 text-sm text-card-foreground shadow-sm transition placeholder:text-muted-foreground",
          error ? "border-destructive" : "border-border focus:border-primary",
          className
        )}
        {...props}
      />
      {error ? (
        <p id={errorId} className="text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  );
}
