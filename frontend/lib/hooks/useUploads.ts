"use client";

import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { authHeaders } from "@/lib/auth-client";
import { UploadSchema, type Upload } from "@/lib/schemas";

export type UploadInput = {
  file: File;
  purpose: string;
};

export type AvatarFetchInput = {
  image_url: string;
};

export function useUploads(): {
  uploads: UseQueryResult<Upload[]>;
  upload: UseMutationResult<Upload, Error, UploadInput>;
  deleteUpload: UseMutationResult<void, Error, string>;
  avatarFetch: UseMutationResult<Upload, Error, AvatarFetchInput>;
} {
  const queryClient = useQueryClient();
  const invalidateUploads = () => {
    void queryClient.invalidateQueries({ queryKey: ["uploads"] });
  };

  const uploads = useQuery({
    queryKey: ["uploads"],
    queryFn: async () => UploadSchema.array().parse(await apiFetch<unknown>("/uploads", { headers: authHeaders() }))
  });

  const upload = useMutation({
    mutationFn: async ({ file, purpose }: UploadInput) => {
      const formData = new FormData();
      formData.set("file", file);
      formData.set("purpose", purpose);
      return UploadSchema.parse(
        await apiFetch<unknown>("/uploads", {
          method: "POST",
          headers: authHeaders(),
          body: formData
        })
      );
    },
    onSuccess: invalidateUploads
  });

  const deleteUpload = useMutation({
    mutationFn: async (uploadId: string) =>
      apiFetch<void>(`/uploads/${uploadId}`, {
        method: "DELETE",
        headers: authHeaders()
      }),
    onSuccess: invalidateUploads
  });

  const avatarFetch = useMutation({
    mutationFn: async (payload: AvatarFetchInput) =>
      UploadSchema.parse(
        await apiFetch<unknown>("/uploads/avatar-fetch", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify(payload)
        })
      ),
    onSuccess: invalidateUploads
  });

  return { uploads, upload, deleteUpload, avatarFetch };
}
