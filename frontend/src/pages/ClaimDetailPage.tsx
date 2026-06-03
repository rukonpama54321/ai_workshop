import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ClaimDetail, deleteClaim, User } from "../api";

function flagClass(flag: string) {
  if (flag === "ok") return "text-green-700";
  if (flag === "non_reimbursable" || flag === "rejected") return "text-red-700";
  if (flag === "mismatch" || flag === "capped") return "text-amber-700";
  return "text-slate-700";
}

export default function ClaimDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [claim, setClaim] = useState<ClaimDetail | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  useEffect(() => {
    api<User>("/auth/me").then(setUser);
    if (id) api<ClaimDetail>(`/claims/${id}`).then(setClaim);
  }, [id]);

  async function review(action: string) {
    if (!id) return;
    setBusy(true);
    try {
      const updated = await api<ClaimDetail>(`/claims/${id}/review`, {
        method: "POST",
        body: JSON.stringify({ action, comment }),
      });
      setClaim(updated);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!id || !claim) return;
    const label = claim.status.replace(/_/g, " ");
    if (!window.confirm(`Delete this claim (${label})? This cannot be undone.`)) return;
    setBusy(true);
    setDeleteError("");
    try {
      await deleteClaim(id);
      navigate("/");
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete claim");
    } finally {
      setBusy(false);
    }
  }

  if (!claim) return <p>Loading…</p>;

  const isReviewer = user?.role === "reviewer" || user?.role === "admin";
  const canReview = isReviewer && ["pending_review", "pending_signoff"].includes(claim.status);
  const canDelete =
    isReviewer ||
    (user?.role === "employee" && claim.status !== "approved");

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Claim calculation</h1>
          <p className="text-sm text-slate-500">Status: {claim.status.replace(/_/g, " ")}</p>
        </div>
        {canDelete && (
          <button
            type="button"
            disabled={busy}
            onClick={handleDelete}
            className="rounded border border-red-300 bg-white px-3 py-1.5 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
          >
            Delete claim
          </button>
        )}
      </div>
      {deleteError && <p className="text-sm text-red-600">{deleteError}</p>}

      {/* Summary panel */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Total claimed</p>
          <p className="text-2xl font-bold">₹{claim.total_claimed.toLocaleString()}</p>
        </div>
        <div className="rounded-lg border border-teal-200 bg-teal-50 p-4 shadow-sm">
          <p className="text-sm text-teal-700">Total claimable</p>
          <p className="text-2xl font-bold text-teal-900">₹{claim.total_claimable.toLocaleString()}</p>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 shadow-sm">
          <p className="text-sm text-red-700">Deductions</p>
          <p className="text-2xl font-bold text-red-900">₹{claim.total_deductions.toLocaleString()}</p>
        </div>
      </div>

      {/* Line items */}
      <section className="rounded-lg border bg-white shadow-sm">
        <h2 className="border-b px-4 py-3 font-semibold">Line items & validation</h2>
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-2">Category</th>
              <th className="px-4 py-2">Description</th>
              <th className="px-4 py-2">Claimed</th>
              <th className="px-4 py-2">Claimable</th>
              <th className="px-4 py-2">Flag</th>
              <th className="px-4 py-2">Deduction note</th>
            </tr>
          </thead>
          <tbody>
            {claim.line_items.map((li) => (
              <tr key={li.id} className={`border-t ${li.review_required ? "bg-amber-50" : ""}`}>
                <td className="px-4 py-2">{li.category}</td>
                <td className="px-4 py-2">{li.description}</td>
                <td className="px-4 py-2">₹{li.amount_claimed.toLocaleString()}</td>
                <td className="px-4 py-2 font-medium">₹{li.amount_claimable.toLocaleString()}</td>
                <td className={`px-4 py-2 font-medium ${flagClass(li.status_flag)}`}>
                  {li.status_flag}
                  {li.review_required && " ⚠"}
                </td>
                <td className="px-4 py-2 text-xs text-slate-600">{li.deduction_comment || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Documents & extraction audit */}
      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-lg border bg-white p-4 shadow-sm">
          <h2 className="mb-2 font-semibold">Documents</h2>
          <ul className="text-sm">
            {claim.documents.map((d) => (
              <li key={d.id}>
                {d.filename} — {d.doc_type || "unclassified"}
              </li>
            ))}
          </ul>
        </section>
        <section className="rounded-lg border bg-white p-4 shadow-sm">
          <h2 className="mb-2 font-semibold">Extraction audit</h2>
          <ul className="space-y-1 text-xs">
            {claim.extraction_fields.map((f, i) => (
              <li key={i}>
                <strong>{f.field_name}:</strong> {f.value ?? "null"}
                {f.confidence != null && ` (${Math.round(f.confidence * 100)}%)`}
                {f.review_required && " — review required"}
              </li>
            ))}
          </ul>
        </section>
      </div>

      {canReview && (
        <section className="rounded-lg border bg-white p-4 shadow-sm">
          <h2 className="mb-3 font-semibold">Reviewer sign-off</h2>
          <textarea
            className="mb-3 w-full rounded border p-2 text-sm"
            rows={3}
            placeholder="Comment (optional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <div className="flex gap-2">
            <button
              disabled={busy}
              onClick={() => review("approve")}
              className="rounded bg-green-700 px-4 py-2 text-white hover:bg-green-800"
            >
              Approve
            </button>
            <button
              disabled={busy}
              onClick={() => review("reject")}
              className="rounded bg-red-700 px-4 py-2 text-white hover:bg-red-800"
            >
              Reject
            </button>
            <button
              disabled={busy}
              onClick={() => review("request_info")}
              className="rounded bg-amber-600 px-4 py-2 text-white hover:bg-amber-700"
            >
              Request info
            </button>
          </div>
        </section>
      )}

      {claim.reviewer_comment && (
        <p className="text-sm text-slate-600">
          <strong>Reviewer note:</strong> {claim.reviewer_comment}
        </p>
      )}
    </div>
  );
}
