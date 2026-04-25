"use client";

import { Dropzone } from "@/components/ui/dropzone";

type UploadDropzoneProps = {
  pending?: boolean;
  onUpload: (file: File) => void;
};

export function UploadDropzone({ pending, onUpload }: UploadDropzoneProps) {
  return (
    <Dropzone
      label={pending ? "Subiendo archivo..." : "Arrastra archivos o selecciona desde disco"}
      description="PDF, CSV e imagenes de soporte. El proposito se marca como general en Phase 2."
      multiple
      disabled={pending}
      onFiles={(files) => {
        const [firstFile] = files;
        if (firstFile) {
          onUpload(firstFile);
        }
      }}
    />
  );
}
