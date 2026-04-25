"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { CartSummary } from "@/components/features/billing/cart-summary";
import { CheckoutButton } from "@/components/features/billing/checkout-button";
import { PlanCard } from "@/components/features/billing/plan-card";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCart } from "@/lib/hooks/useCart";
import { useCheckout } from "@/lib/hooks/useCheckout";
import { usePlans } from "@/lib/hooks/usePlans";
import type { Plan } from "@/lib/schemas";

const fallbackPlans: Plan[] = [
  {
    id: "00000000-0000-4000-8000-000000000101",
    code: "free",
    name: "Free",
    monthly_price_cents: 0,
    currency: "USD",
    description: "Para validar el flujo con una organizacion y volumen minimo."
  },
  {
    id: "00000000-0000-4000-8000-000000000102",
    code: "pro",
    name: "Pro",
    monthly_price_cents: 900,
    currency: "USD",
    description: "Automatizacion operativa, webhooks y reportes para equipos pequenos."
  },
  {
    id: "00000000-0000-4000-8000-000000000103",
    code: "enterprise",
    name: "Enterprise",
    monthly_price_cents: 0,
    currency: "USD",
    description: "Contacto comercial, integraciones privadas y soporte dedicado."
  }
];

export default function BillingPage() {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const { data: plans = fallbackPlans, isLoading: plansLoading } = usePlans();
  const { cart, setPlan, applyCoupon, removeCoupon } = useCart();
  const checkout = useCheckout();

  const selectedPlanId = cart.data?.plan_id;

  async function selectPlan(plan: Plan): Promise<void> {
    setMessage(null);
    try {
      await setPlan.mutateAsync({ plan_id: plan.id, quantity: cart.data?.quantity ?? 1 });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo seleccionar el plan");
    }
  }

  async function checkoutCart(): Promise<void> {
    setMessage(null);
    try {
      await checkout.mutateAsync();
      router.push("/billing/invoices");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo confirmar el checkout");
    }
  }

  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Billing</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Facturacion</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="grid gap-4">
          <div className="grid gap-4 md:grid-cols-3">
            {plansLoading
              ? fallbackPlans.map((plan) => <Skeleton key={plan.id} className="h-72" />)
              : plans.map((plan) => <PlanCard key={plan.id} plan={plan} selected={selectedPlanId === plan.id} onSelect={selectPlan} />)}
          </div>
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Flujo de checkout</h2>
              <p className="text-sm text-muted-foreground">Phase 2 usa pago mockeado y emite invoice al confirmar.</p>
            </CardHeader>
            <CardContent>
              <CheckoutButton disabled={!cart.data || checkout.isPending} pending={checkout.isPending} onCheckout={checkoutCart} />
              {message ? <p className="mt-3 text-sm text-destructive">{message}</p> : null}
            </CardContent>
          </Card>
        </div>

        <CartSummary
          cart={cart.data}
          plans={plans}
          disabled={setPlan.isPending || applyCoupon.isPending || removeCoupon.isPending}
          onQuantityChange={(quantity) => {
            if (cart.data) {
              void setPlan.mutateAsync({ plan_id: cart.data.plan_id, quantity });
            }
          }}
          onApplyCoupon={(coupon_code) => void applyCoupon.mutateAsync({ coupon_code })}
          onRemoveCoupon={(couponCode) => void removeCoupon.mutateAsync(couponCode)}
        />
      </div>
    </section>
  );
}
