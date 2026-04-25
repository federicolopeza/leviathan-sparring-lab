"use client";

import type { ComponentProps, ReactNode } from "react";
import {
  Controller,
  FormProvider,
  type ControllerProps,
  type FieldPath,
  type FieldValues,
  type UseFormReturn
} from "react-hook-form";
import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";

export function Form<TFieldValues extends FieldValues>({
  form,
  children
}: {
  form: UseFormReturn<TFieldValues>;
  children: ReactNode;
}) {
  return <FormProvider {...form}>{children}</FormProvider>;
}

export function FormField<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
>(props: ControllerProps<TFieldValues, TName>) {
  return <Controller {...props} />;
}

export function FormItem({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("grid gap-2", className)}>{children}</div>;
}

export function FormLabel({ className, ...props }: ComponentProps<typeof Label>) {
  return <Label className={cn(className)} {...props} />;
}

export function FormControl({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("grid gap-2", className)}>{children}</div>;
}

export function FormMessage({ message }: { message?: string }) {
  if (!message) {
    return null;
  }

  return <p className="text-sm text-destructive">{message}</p>;
}
