import { describe, expect, it } from "vitest";
import { nextWebhookEvents } from "@/components/features/webhooks/webhook-form";

describe("webhook form", () => {
  it("updates events checkbox state", () => {
    const initial = ["invoice.issued"];
    const added = nextWebhookEvents(initial, "invoice.paid", true);
    const removed = nextWebhookEvents(added, "invoice.issued", false);

    expect(added).toEqual(["invoice.issued", "invoice.paid"]);
    expect(removed).toEqual(["invoice.paid"]);
  });
});
