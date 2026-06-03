const TOKEN_KEY = "medclaim_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }

  const res = await fetch(`/api${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json();
}

export async function deleteClaim(claimId: string): Promise<void> {
  await api<void>(`/claims/${claimId}`, { method: "DELETE" });
}

export async function login(username: string, password: string) {
  const body = new URLSearchParams({ username, password });
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error("Invalid credentials");
  const data = await res.json();
  setToken(data.access_token);
}

export interface User {
  id: string;
  username: string;
  role: string;
  full_name: string;
  job_group: string;
  city_class: string;
  employee_category: string;
}

export interface ClaimSummary {
  id: string;
  status: string;
  claim_type: string | null;
  submission_date: string;
  total_claimed: number;
  total_claimable: number;
  total_deductions: number;
  employee_name?: string;
  has_review_flags: boolean;
}

export interface LineItem {
  id: string;
  category: string;
  description: string;
  amount_claimed: number;
  amount_claimable: number;
  limit_applied: number | null;
  status_flag: string;
  deduction_comment: string | null;
  review_required: boolean;
}

export interface ClaimDetail extends ClaimSummary {
  summary_json: Record<string, unknown> | null;
  reviewer_comment: string | null;
  line_items: LineItem[];
  documents: { id: string; filename: string; doc_type: string | null }[];
  extraction_fields: {
    field_name: string;
    value: string | null;
    confidence: number | null;
    review_required: boolean;
  }[];
}
