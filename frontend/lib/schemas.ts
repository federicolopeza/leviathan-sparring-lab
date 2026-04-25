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
  id: z.string(),
  email: z.email(),
  name: z.string(),
  role: z.string(),
  org_id: z.string().optional()
});

export const OrgSchema = z.object({
  id: z.string(),
  name: z.string(),
  plan: z.enum(["free", "pro", "enterprise"]),
  region: z.string()
});

export type LoginInput = z.infer<typeof LoginSchema>;
export type SignupInput = z.infer<typeof SignupSchema>;
export type User = z.infer<typeof UserSchema>;
export type Org = z.infer<typeof OrgSchema>;
