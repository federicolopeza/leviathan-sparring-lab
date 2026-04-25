"use client";

import { Minus, Plus, X } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { Cart, Plan } from "@/lib/schemas";

type CartSummaryProps = {
  cart?: Cart;
  plans: Plan[];
  onQuantityChange: (quantity: number) => void;
  onApplyCoupon: (couponCode: string) => void;
  onRemoveCoupon: (couponCode: string) => void;
  disabled?: boolean;
};

export function formatMoney(cents: number, currency = "USD"): string {
  return new Intl.NumberFormat("es-UY", { style: "currency", currency }).format(cents / 100);
}

export function CartSummary({ cart, plans, onQuantityChange, onApplyCoupon, onRemoveCoupon, disabled }: CartSummaryProps) {
  const [couponCode, setCouponCode] = useState("");
  const plan = plans.find((item) => item.id === cart?.plan_id);

  function onSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextCode = couponCode.trim();
    if (!nextCode) {
      return;
    }
    onApplyCoupon(nextCode);
    setCouponCode("");
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="text-xl font-semibold">Carrito</h2>
        <p className="text-sm text-muted-foreground">Ajusta plan, cantidad y cupones antes de confirmar.</p>
      </CardHeader>
      <CardContent className="grid gap-5">
        <div className="rounded-lg border border-border bg-muted p-4">
          <p className="text-sm text-muted-foreground">Plan actual</p>
          <p className="mt-1 font-semibold">{plan?.name ?? "Sin plan seleccionado"}</p>
        </div>

        <div className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
          <span className="text-sm font-medium">Cantidad</span>
          <div className="flex items-center gap-2">
            <Button type="button" size="sm" variant="secondary" disabled={disabled || !cart || cart.quantity <= 1} onClick={() => onQuantityChange((cart?.quantity ?? 1) - 1)}>
              <Minus className="h-4 w-4" />
            </Button>
            <span className="grid h-9 min-w-12 place-items-center rounded-lg bg-muted px-3 text-sm font-semibold">{cart?.quantity ?? 1}</span>
            <Button type="button" size="sm" variant="secondary" disabled={disabled || !cart} onClick={() => onQuantityChange((cart?.quantity ?? 1) + 1)}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <form className="grid gap-3 sm:grid-cols-[1fr_auto]" onSubmit={onSubmit}>
          <Input label="Cupon" value={couponCode} onChange={(event) => setCouponCode(event.target.value)} placeholder="PRO-LATAM" />
          <Button type="submit" className="self-end" disabled={disabled || !couponCode.trim()}>
            Aplicar
          </Button>
        </form>

        <div className="flex flex-wrap gap-2">
          {cart?.applied_coupons.map((coupon) => (
            <Badge key={coupon.coupon_id} variant="success" className="gap-2">
              {coupon.coupon_code}
              <button type="button" aria-label={`Quitar cupon ${coupon.coupon_code}`} onClick={() => onRemoveCoupon(coupon.coupon_code)}>
                <X className="h-3.5 w-3.5" />
              </button>
            </Badge>
          ))}
        </div>

        <dl className="grid gap-2 border-t border-border pt-4 text-sm">
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Subtotal</dt>
            <dd>{formatMoney(cart?.subtotal_cents ?? 0, plan?.currency)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Descuento</dt>
            <dd>-{formatMoney(cart?.discount_cents ?? 0, plan?.currency)}</dd>
          </div>
          <div className="flex justify-between text-base font-semibold">
            <dt>Total</dt>
            <dd>{formatMoney(cart?.total_cents ?? 0, plan?.currency)}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
