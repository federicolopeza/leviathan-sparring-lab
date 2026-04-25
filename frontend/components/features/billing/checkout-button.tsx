"use client";

import { CreditCard } from "lucide-react";
import { Button } from "@/components/ui/button";

type CheckoutButtonProps = {
  disabled?: boolean;
  pending?: boolean;
  onCheckout: () => void;
};

export function CheckoutButton({ disabled, pending, onCheckout }: CheckoutButtonProps) {
  return (
    <Button type="button" size="lg" className="w-full" disabled={disabled || pending} onClick={onCheckout}>
      <CreditCard className="h-4 w-4" />
      {pending ? "Confirmando..." : "Confirmar checkout"}
    </Button>
  );
}
