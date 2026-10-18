"use client";

import { useRef, useState } from "react";
import { extractPdfText } from "@/lib/api";

interface Props {
  id: string;
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  maxLength: number;
  hint: string;
}

type Upload =
  | { state: "idle" }
  | { state: "reading"; name: string }
  | { state: "done"; name: string; pages: number }
  | { state: "error"; message: string };

// A text area that also accepts a PDF, via the upload button or drag-and-drop.
// The extracted text lands in the text area so the user can review and edit it.
export default function TextInput({ id, label, placeholder, value, onChange, maxLength, hint }: Props) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [upload, setUpload] = useState<Upload>({ state: "idle" });
  const [dragging, setDragging] = useState(false);
  const reading = upload.state === "reading";

  async function handleFile(file: File | undefined) {
    if (!file || reading) return;
    setUpload({ state: "reading", name: file.name });
    try {
      const { text, pages } = await extractPdfText(file);
      if (text.length > maxLength) {
        throw new Error(
          `This PDF has ${text.length.toLocaleString()} characters of text; the limit is ${maxLength.toLocaleString()}. Paste only the relevant part instead.`,
        );
      }
      onChange(text);
      setUpload({ state: "done", name: file.name, pages });
    } catch (e) {
      setUpload({ state: "error", message: e instanceof Error ? e.message : "Couldn't read this PDF." });
    }
  }

  return (
    <div className="field">
      <div className="field-head">
        <label htmlFor={id}>{label}</label>
        <button
          type="button"
          className="secondary small"
          onClick={() => fileInput.current?.click()}
          disabled={reading}
        >
          {reading ? "Reading PDF…" : "Upload PDF"}
        </button>
        <input
          ref={fileInput}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          onChange={(e) => {
            handleFile(e.target.files?.[0]);
            e.target.value = ""; // allow re-selecting the same file
          }}
        />
      </div>
      <span className="hint muted" id={`${id}-hint`}>{hint}</span>

      <div
        className={`dropzone ${dragging ? "dragging" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFile(e.dataTransfer.files?.[0]);
        }}
      >
        <textarea
          id={id}
          placeholder={`${placeholder}\n\nOr use “Upload PDF” above.`}
          value={value}
          maxLength={maxLength}
          aria-describedby={`${id}-hint ${id}-status`}
          disabled={reading}
          onChange={(e) => {
            onChange(e.target.value);
            if (upload.state === "error") setUpload({ state: "idle" });
          }}
        />
        {dragging && <div className="drop-overlay">Drop PDF to load its text</div>}
        {reading && <div className="drop-overlay"><span className="spinner" aria-hidden /> Reading {upload.name}…</div>}
      </div>

      <div className="field-foot" id={`${id}-status`} aria-live="polite">
        {upload.state === "done" && (
          <span className="upload-ok">
            ✓ Loaded {upload.name} ({upload.pages} page{upload.pages === 1 ? "" : "s"}). Check the text above.
          </span>
        )}
        {upload.state === "error" && <span className="upload-error">{upload.message}</span>}
        <span className="char-count muted">
          {value.length.toLocaleString()} / {maxLength.toLocaleString()}
        </span>
      </div>
    </div>
  );
}
