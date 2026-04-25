import { describe, expect, it, vi } from "vitest";
import { filesFromList } from "@/components/ui/dropzone";

describe("uploads dropzone", () => {
  it("file drop triggers upload", () => {
    const upload = vi.fn();
    const file = new File(["id,total"], "invoice.csv", { type: "text/csv" });
    const fileList = {
      0: file,
      length: 1,
      item: (index: number) => (index === 0 ? file : null),
      [Symbol.iterator]: function* iterator() {
        yield file;
      }
    } as FileList;

    filesFromList(fileList).forEach(upload);

    expect(upload).toHaveBeenCalledWith(file);
  });
});
