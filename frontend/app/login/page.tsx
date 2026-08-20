"use client";
import { FormEvent, useState } from "react";
import { login, saveToken, saveRefreshToken } from "../../lib/api";

export default function LoginPage() {
  const [email,setEmail]=useState(""); const [password,setPassword]=useState(""); const [error,setError]=useState(""); const [busy,setBusy]=useState(false);
  async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError("");try{const t=await login(email,password);saveToken(t.access_token);saveRefreshToken(t.refresh_token);window.location.href="/";}catch(err){setError(err instanceof Error?err.message:"Unable to sign in");}finally{setBusy(false)}}
  return <main className="auth-page"><div className="auth-card"><h1>Welcome back</h1><p>Sign in to continue with Sanjeevani.</p><form onSubmit={submit}><label>Email<input type="email" required value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email"/></label><label>Password<input type="password" required value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password"/></label>{error&&<p role="alert" className="error">{error}</p>}<button disabled={busy}>{busy?"Signing in…":"Sign in"}</button></form><a href="/reset-password">Forgot password?</a></div></main>
}
