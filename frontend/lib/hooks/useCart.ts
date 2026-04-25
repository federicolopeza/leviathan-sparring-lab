"use client";

import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { authHeaders } from "@/lib/auth-client";
import { CartSchema, type Cart } from "@/lib/schemas";

export type SetPlanInput = {
  plan_id: string;
  quantity: number;
};

export type CouponInput = {
  coupon_code: string;
};

export function computeCartTotal(cart: Pick<Cart, "subtotal_cents" | "discount_cents" | "total_cents">): number {
  return cart.total_cents ?? Math.max(0, cart.subtotal_cents - cart.discount_cents);
}

export function useCart(): {
  cart: UseQueryResult<Cart>;
  setPlan: UseMutationResult<Cart, Error, SetPlanInput>;
  applyCoupon: UseMutationResult<Cart, Error, CouponInput>;
  removeCoupon: UseMutationResult<Cart, Error, string>;
  clearCart: UseMutationResult<void, Error, void>;
} {
  const queryClient = useQueryClient();
  const invalidateCart = () => {
    void queryClient.invalidateQueries({ queryKey: ["billing", "cart"] });
  };

  const cart = useQuery({
    queryKey: ["billing", "cart"],
    queryFn: async () => CartSchema.parse(await apiFetch<unknown>("/billing/cart", { headers: authHeaders() }))
  });

  const setPlan = useMutation({
    mutationFn: async (payload: SetPlanInput) =>
      CartSchema.parse(
        await apiFetch<unknown>("/billing/cart/plan", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify(payload)
        })
      ),
    onSuccess: (nextCart) => {
      queryClient.setQueryData(["billing", "cart"], nextCart);
    }
  });

  const applyCoupon = useMutation({
    mutationFn: async (payload: CouponInput) =>
      CartSchema.parse(
        await apiFetch<unknown>("/billing/cart/coupons", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify(payload)
        })
      ),
    onSuccess: (nextCart) => {
      queryClient.setQueryData(["billing", "cart"], nextCart);
    }
  });

  const removeCoupon = useMutation({
    mutationFn: async (couponCode: string) =>
      CartSchema.parse(
        await apiFetch<unknown>(`/billing/cart/coupons/${encodeURIComponent(couponCode)}`, {
          method: "DELETE",
          headers: authHeaders()
        })
      ),
    onSuccess: (nextCart) => {
      queryClient.setQueryData(["billing", "cart"], nextCart);
    }
  });

  const clearCart = useMutation({
    mutationFn: async () =>
      apiFetch<void>("/billing/cart", {
        method: "DELETE",
        headers: authHeaders()
      }),
    onSuccess: invalidateCart
  });

  return { cart, setPlan, applyCoupon, removeCoupon, clearCart };
}
