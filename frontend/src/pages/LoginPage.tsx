import { FormEvent, useState } from "react";
import { api, login, User } from "../api";

export default function LoginPage({ onLogin }: { onLogin: (u: User) => void }) {
  const [username, setUsername] = useState("employee_workman");
  const [password, setPassword] = useState("demo123");
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await login(username, password);
      const user = await api<User>("/auth/me");
      onLogin(user);
    } catch {
      setError("Invalid credentials");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-teal-50 to-slate-100">
      <form onSubmit={handleSubmit} className="w-full max-w-md rounded-xl bg-white p-8 shadow-lg">
        <h1 className="mb-2 text-2xl font-bold text-teal-900">Workshop Login</h1>
        <p className="mb-6 text-sm text-slate-500">
          Demo: employee_workman / employee_mgmt / reviewer — password demo123
        </p>
        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
        <label className="mb-2 block text-sm font-medium">Username</label>
        <input
          className="mb-4 w-full rounded border px-3 py-2"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <label className="mb-2 block text-sm font-medium">Password</label>
        <input
          type="password"
          className="mb-6 w-full rounded border px-3 py-2"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit" className="w-full rounded bg-teal-700 py-2 text-white hover:bg-teal-800">
          Sign in
        </button>
      </form>
    </div>
  );
}
