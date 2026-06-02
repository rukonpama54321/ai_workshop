import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ClaimSummary } from "../api";

export default function NewClaimPage() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!files?.length) return;
    setBusy(true);
    setError("");
    const form = new FormData();
    Array.from(files).forEach((f) => form.append("files", f));
    try {
      const res = await fetch("/api/claims", {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("medclaim_token")}` },
        body: form,
      });
      if (!res.ok) throw new Error("Upload failed");
      const claim: ClaimSummary = await res.json();
      navigate(`/claims/${claim.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-xl">
      <h1 className="mb-4 text-2xl font-bold">Submit new claim</h1>
      <p className="mb-4 text-sm text-slate-600">
        Upload PDF or image files (hospital bill, prescription, discharge summary). Processing uses
        local Ollama if available, otherwise regex fallback.
      </p>
      <form onSubmit={handleSubmit} className="rounded-lg border bg-white p-6 shadow-sm">
        <input
          type="file"
          multiple
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={(e) => setFiles(e.target.files)}
          className="mb-4 w-full"
        />
        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={busy || !files?.length}
          className="rounded bg-teal-700 px-4 py-2 text-white disabled:opacity-50"
        >
          {busy ? "Processing…" : "Upload & validate"}
        </button>
      </form>
    </div>
  );
}
