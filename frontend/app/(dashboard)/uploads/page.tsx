"use client";

import { Download, Trash2 } from "lucide-react";
import { useState } from "react";
import { AvatarFetchForm } from "@/components/features/uploads/avatar-fetch-form";
import { UploadDropzone } from "@/components/features/uploads/upload-dropzone";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { DataTable } from "@/components/ui/data-table";
import { Skeleton } from "@/components/ui/skeleton";
import { useUploads } from "@/lib/hooks/useUploads";

function formatBytes(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadsPage() {
  const [message, setMessage] = useState<string | null>(null);
  const { uploads, upload, deleteUpload, avatarFetch } = useUploads();

  async function uploadFile(file: File): Promise<void> {
    setMessage(null);
    try {
      await upload.mutateAsync({ file, purpose: "general" });
      setMessage("Archivo cargado.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo cargar el archivo");
    }
  }

  async function fetchAvatar(image_url: string): Promise<void> {
    setMessage(null);
    try {
      await avatarFetch.mutateAsync({ image_url });
      setMessage("Avatar importado desde URL.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo importar el avatar");
    }
  }

  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Uploads</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Archivos</h1>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Carga segura</h2>
          <p className="text-sm text-muted-foreground">Ingesta de CSV, contratos y soportes de conciliacion.</p>
        </CardHeader>
        <CardContent className="grid gap-5">
          <UploadDropzone pending={upload.isPending} onUpload={uploadFile} />
          <AvatarFetchForm pending={avatarFetch.isPending} onFetch={fetchAvatar} />
          {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Archivos cargados</h2>
        </CardHeader>
        <CardContent>
          {uploads.isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <DataTable
              rows={uploads.data ?? []}
              getRowId={(item) => item.id}
              emptyLabel="Todavia no hay archivos cargados."
              page={1}
              hasNextPage={false}
              onPageChange={() => undefined}
              columns={[
                { key: "name", header: "Nombre", cell: (item) => item.original_filename },
                { key: "purpose", header: "Proposito", cell: (item) => item.purpose },
                { key: "size", header: "Tamano", cell: (item) => formatBytes(item.size_bytes) },
                { key: "date", header: "Fecha", cell: (item) => new Date(item.created_at).toLocaleDateString("es-UY") },
                {
                  key: "download",
                  header: "Descargar",
                  cell: () => (
                    <Button type="button" variant="secondary" size="sm" disabled title="TODO Phase 3">
                      <Download className="h-4 w-4" />
                      Descargar
                    </Button>
                  )
                },
                {
                  key: "delete",
                  header: "Eliminar",
                  cell: (item) => (
                    <Button type="button" variant="destructive" size="sm" disabled={deleteUpload.isPending} onClick={() => void deleteUpload.mutateAsync(item.id)}>
                      <Trash2 className="h-4 w-4" />
                      Eliminar
                    </Button>
                  )
                }
              ]}
            />
          )}
        </CardContent>
      </Card>
    </section>
  );
}
