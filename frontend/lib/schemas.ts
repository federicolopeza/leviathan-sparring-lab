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

export type LoginInput = z.infer<typeof LoginSchema>;
export type SignupInput = z.infer<typeof SignupSchema>;
export type User = z.infer<typeof UserSchema>;
export type Org = z.infer<typeof OrgSchema>;
export type Membership = z.infer<typeof MembershipSchema>;
export type Invitation = z.infer<typeof InvitationSchema>;
