import { isValidElement, type ReactElement } from "react";
import type { UseQueryResult } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { AuthGate } from "@/components/auth/auth-gate";
import { ApiError } from "@/lib/api";
import type { User } from "@/lib/schemas";

const mocks = vi.hoisted(() => ({
  replace: vi.fn(),
  userResult: {} as Partial<UseQueryResult<User>>
}));

vi.mock("react", async (importOriginal: () => Promise<typeof import("react")>) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useEffect: (effect: () => void | (() => void)) => {
      effect();
    }
  };
});

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({ replace: mocks.replace })
}));

vi.mock("@/lib/hooks/useUser", () => ({
  useUser: () => mocks.userResult
}));

describe("AuthGate", () => {
  it("redirects when useUser returns 401", () => {
    mocks.userResult = {
      data: undefined,
      error: new ApiError(401, "Not Found"),
      isLoading: false,
      isFetching: false
    };

    AuthGate({ children: "Privado" });

    expect(mocks.replace).toHaveBeenCalledWith("/login?redirect=%2Fdashboard");
  });

  it("renders children when user is present", () => {
    mocks.userResult = {
      data: {
        id: "00000000-0000-4000-8000-000000000001",
        email: "user@melispy.com",
        name: "Melispy User",
        bio: null,
        avatar_url: null,
        is_admin: false,
        email_verified: true
      },
      error: null,
      isLoading: false,
      isFetching: false
    };

    const result = AuthGate({ children: "Privado" });

    expect(isValidElement(result)).toBe(true);
    expect((result as ReactElement<{ children: string }>).props.children).toBe("Privado");
  });
});
