"use client";

import { UploadCloud } from "lucide-react";
import { useRef, useState, type DragEvent, type InputHTMLAttributes, type MutableRefObject, type Ref } from "react";
import { cn } from "@/lib/utils";

type DropzoneProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "onChange"> & {
  ref?: Ref<HTMLInputElement>;
  label: string;
  description: string;
  onFiles: (files: File[]) => void;
};

export function filesFromList(fileList: FileList | null): File[] {
  return fileList ? Array.from(fileList) : [];
}

export function Dropzone({ className, label, description, onFiles, ref, ...props }: DropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragging, setDragging] = useState(false);

  function openPicker(): void {
    inputRef.current?.click();
  }

  function onDrop(event: DragEvent<HTMLButtonElement>): void {
    event.preventDefault();
    setDragging(false);
    onFiles(filesFromList(event.dataTransfer.files));
  }

  return (
    <button
      type="button"
      className={cn(
        "grid min-h-48 w-full place-items-center rounded-lg border border-dashed px-6 py-10 text-center transition",
        dragging ? "border-primary bg-primary/10" : "border-border bg-muted/70 hover:border-primary",
        className
      )}
      onClick={openPicker}
      onDragEnter={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <span className="grid justify-items-center gap-3">
        <UploadCloud className="h-10 w-10 text-primary" aria-hidden="true" />
        <span className="font-semibold">{label}</span>
        <span className="max-w-md text-sm text-muted-foreground">{description}</span>
      </span>
      <input
        ref={(node) => {
          inputRef.current = node;
          if (typeof ref === "function") {
            ref(node);
          } else if (ref) {
            (ref as MutableRefObject<HTMLInputElement | null>).current = node;
          }
        }}
        className="sr-only"
        type="file"
        onChange={(event) => onFiles(filesFromList(event.currentTarget.files))}
        {...props}
      />
    </button>
  );
}
