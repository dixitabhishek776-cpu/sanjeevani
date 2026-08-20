"use client";
import { FormEvent, useState } from "react";
import { verifyEmail } from "../../lib/api";
export default function VerifyPage(){const [token,setToken]=useState("");const [message,setMessage]=useState("");async function submit(e:FormEvent){e.preventDefault();try{await verifyEmail(token);setMessage("Your email is verified. You can sign in now.")}catch(err){setMessage(err instanceof Error?err.message:"Verification failed")}}return <main className="auth-page"><div className="auth-card"><h1>Verify email</h1><form onSubmit={submit}><label>Verification token<input required value={token} onChange={e=>setToken(e.target.value)}/></label><button>Verify</button></form>{message&&<p role="status">{message}</p>}<a href="/login">Go to sign in</a></div></main>}
