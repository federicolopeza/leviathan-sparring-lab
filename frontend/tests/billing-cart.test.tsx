import { describe, expect, it } from "vitest";
import { formatMoney } from "@/components/features/billing/cart-summary";
import { computeCartTotal } from "@/lib/hooks/useCart";
import { CartSchema } from "@/lib/schemas";

describe("billing cart", () => {
  it("applies coupon and computes total", () => {
    const cart = CartSchema.parse({
      id: "00000000-0000-4000-8000-000000000201",
      plan_id: "00000000-0000-4000-8000-000000000102",
      quantity: 2,
      applied_coupons: [{ coupon_code: "PRO-LATAM", coupon_id: "00000000-0000-4000-8000-000000000301" }],
      subtotal_cents: 1800,
      discount_cents: 900,
      total_cents: 900
    });

    expect(cart.applied_coupons[0]?.coupon_code).toBe("PRO-LATAM");
    expect(computeCartTotal(cart)).toBe(900);
    expect(formatMoney(cart.total_cents)).toContain("9");
  });
});
