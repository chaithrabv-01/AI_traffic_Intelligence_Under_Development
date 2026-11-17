import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.jsx";
import { errMsg } from "../services/api.js";

export default function Login() {
  const { user, login } = useAuth();
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(username, password);
      nav("/");
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <h1 className="page-title">Traffic Intelligence</h1>
        <p className="page-sub">Log in to see traffic from your cameras and datasets.</p>
        <label className="form-label">Username</label>
        <input className="form-control mb-3" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus required />
        <label className="form-label">Password</label>
        <input className="form-control mb-3" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <div className="alert alert-danger py-2">{error}</div>}
        <button className="btn btn-primary w-100" disabled={busy}>{busy ? "Logging in..." : "Log in"}</button>
      </form>
    </div>
  );
}
