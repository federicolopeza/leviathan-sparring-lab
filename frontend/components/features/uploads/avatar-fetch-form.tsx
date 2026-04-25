"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type AvatarFetchFormProps = {
  pending?: boolean;
  onFetch: (imageUrl: string) => void;
};

export function AvatarFetchForm({ pending, onFetch }: AvatarFetchFormProps) {
  const [imageUrl, setImageUrl] = useState("");

  function onSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextUrl = imageUrl.trim();
    if (!nextUrl) {
      return;
    }
    onFetch(nextUrl);
  }

  return (
    <form className="grid gap-3 sm:grid-cols-[1fr_auto]" onSubmit={onSubmit}>
      <Input
        label="Avatar desde URL"
        name="image_url"
        type="url"
        value={imageUrl}
        onChange={(event) => setImageUrl(event.target.value)}
        placeholder="https://example.com/avatar.png"
      />
      <Button type="submit" className="self-end" disabled={pending || !imageUrl.trim()}>
        {pending ? "Buscando..." : "Importar avatar"}
      </Button>
    </form>
  );
}
