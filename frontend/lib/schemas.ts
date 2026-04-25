import { z } from "zod";

export const LoginSchema = z.object({
  email: z.email(),
  password: z.string().min(1, "La contrasena es requerida")
});

// SYNC: services/auth-service/app/schemas/auth.py:SignupRequest
export const SignupSchema = z.object({
  name: z.string().min(2, "Ingresa tu nombre"),
  email: z.email(),
  password: z.string().min(8, "Minimo 8 caracteres"),
  org_name: z.string().min(2, "Ingresa el nombre de la organizacion")
});

export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string(),
  bio: z.string().nullable(),
  avatar_url: z.string().nullable(),
  is_admin: z.boolean(),
  email_verified: z.boolean()
});

export const OrgSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  plan: z.enum(["free", "pro", "enterprise"]),
  region: z.string(),
  owner_user_id: z.string().uuid(),
  created_at: z.string()
});

export const MembershipSchema = z.object({
  user_id: z.string().uuid(),
  role: z.enum(["owner", "admin", "member"]),
  created_at: z.string()
});

export const InvitationSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(["owner", "admin", "member"]),
  expires_at: z.string(),
  used_at: z.string().nullable()
});

// SYNC: services/billing-service/app/schemas/billing.py:PlanResponse
export const PlanSchema = z.object({
  id: z.string().uuid(),
  code: z.enum(["free", "pro", "enterprise"]),
  name: z.string(),
  monthly_price_cents: z.number().int(),
  currency: z.string(),
  description: z.string()
});

// SYNC: services/billing-service/app/schemas/billing.py:CartResponse
export const CartSchema = z.object({
  id: z.string().uuid(),
  plan_id: z.string().uuid(),
  quantity: z.number().int(),
  applied_coupons: z
    .object({
      coupon_code: z.string(),
      coupon_id: z.string().uuid()
    })
    .array(),
  subtotal_cents: z.number().int(),
  discount_cents: z.number().int(),
  total_cents: z.number().int()
});

// SYNC: services/billing-service/app/schemas/billing.py:CheckoutResponse
export const CheckoutSchema = z.object({
  id: z.string().uuid(),
  status: z.string(),
  total_cents: z.number().int(),
  completed_at: z.string().nullable()
});

// SYNC: services/billing-service/app/schemas/billing.py:InvoiceResponse
export const InvoiceSchema = z.object({
  id: z.string().uuid(),
  number: z.string(),
  total_cents: z.number().int(),
  status: z.string(),
  issued_at: z.string()
});

// SYNC: services/uploads-service/app/schemas/uploads.py:UploadResponse
export const UploadSchema = z.object({
  id: z.string().uuid(),
  original_filename: z.string(),
  purpose: z.string(),
  size_bytes: z.number().int(),
  created_at: z.string()
});

// SYNC: services/webhooks-service/app/schemas/webhooks.py:WebhookResponse
export const WebhookSchema = z.object({
  id: z.string().uuid(),
  url: z.string(),
  events: z.string().array(),
  created_at: z.string(),
  deleted_at: z.string().nullable()
});

// SYNC: services/webhooks-service/app/schemas/webhooks.py:WebhookDeliveryResponse
export const WebhookDeliverySchema = z.object({
  id: z.string().uuid(),
  event_type: z.string(),
  status: z.string(),
  attempt_count: z.number().int(),
  last_attempted_at: z.string()
});

// SYNC: services/agents-service
export const AgentRunSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  status: z.enum(["queued", "running", "completed", "failed", "cancelled"]),
  input_json: z.record(z.unknown()),
  output_json: z.record(z.unknown()).nullable(),
  created_at: z.string()
});
export type AgentRun = z.infer<typeof AgentRunSchema>;

// SYNC: services/llm-service
export const ConversationSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  model: z.string(),
  created_at: z.string()
});
export type Conversation = z.infer<typeof ConversationSchema>;

export const MessageSchema = z.object({
  id: z.string().uuid(),
  role: z.enum(["user", "assistant", "system"]),
  content: z.string(),
  created_at: z.string()
});
export type Message = z.infer<typeof MessageSchema>;

export type LoginInput = z.infer<typeof LoginSchema>;
export type SignupInput = z.infer<typeof SignupSchema>;
export type User = z.infer<typeof UserSchema>;
export type Org = z.infer<typeof OrgSchema>;
export type Membership = z.infer<typeof MembershipSchema>;
export type Invitation = z.infer<typeof InvitationSchema>;
export type Plan = z.infer<typeof PlanSchema>;
export type Cart = z.infer<typeof CartSchema>;
export type Checkout = z.infer<typeof CheckoutSchema>;
export type Invoice = z.infer<typeof InvoiceSchema>;
export type Upload = z.infer<typeof UploadSchema>;
export type Webhook = z.infer<typeof WebhookSchema>;
export type WebhookDelivery = z.infer<typeof WebhookDeliverySchema>;
