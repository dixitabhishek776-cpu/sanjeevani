const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
let accessToken: string | null = typeof window !== "undefined" ? sessionStorage.getItem("mb_access") : null;

export async function api(path: string, init: RequestInit = {}): Promise<any> {
  const headers = new Headers(init.headers || {});
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  Object.entries(authHeaders()).forEach(([k,v]) => headers.set(k,v));
  let res = await fetch(`${API_BASE}${path}`, {...init, headers, credentials:"include"});
  if (res.status === 401 && path !== "/v1/auth/refresh" && await refreshAccessToken()) {
    const retryHeaders = new Headers(init.headers || {});
    if (init.body && !retryHeaders.has("Content-Type")) retryHeaders.set("Content-Type", "application/json");
    Object.entries(authHeaders()).forEach(([k,v]) => retryHeaders.set(k,v));
    res = await fetch(`${API_BASE}${path}`, {...init, headers: retryHeaders, credentials:"include"});
  }
  if (!res.ok) { const data = await res.json().catch(()=>null); throw new Error(data?.detail || `Request failed (${res.status})`); }
  if (res.status === 204) return null;
  return res.json();
}

export interface SafetyInfo {
  concern_level: "low" | "moderate" | "high" | "immediate";
  resources_shown: boolean;
}

export interface ChatResponse {
  message_id: string;
  chat_id: string;
  ai_response: string;
  resources_text: string | null;
  safety: SafetyInfo;
}

function authHeaders(): Record<string, string> {
  const token = accessToken;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function register(email: string, password: string, displayName?: string) {
  const res = await fetch(`${API_BASE}/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, display_name: displayName || undefined }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail || "Registration failed");
  }
  return res.json();
}

export async function login(email: string, password: string): Promise<{access_token:string;refresh_token:string|null}> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);

  const res = await fetch(`${API_BASE}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    credentials: "include",
    body: form,
  });
  if (!res.ok) { const data = await res.json().catch(()=>null); throw new Error(data?.detail || "Login failed"); }
  return res.json();
}

export async function sendMessage(content: string, chatId?: string): Promise<ChatResponse> {
  const idempotencyKey = (typeof crypto !== "undefined" && "randomUUID" in crypto)
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return api("/v1/chat/message", {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({ content, chat_id: chatId }),
  });
}

export async function logMood(mood_score: number, tags: string[], note?: string) {
  const res = await fetch(`${API_BASE}/v1/mood`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() }, credentials: "include",
    body: JSON.stringify({ mood_score, tags, note }),
  });
  if (!res.ok) throw new Error("Mood log failed");
  return res.json();
}

export interface Alert {
  id: string;
  status: string;
  concern_level: "low" | "moderate" | "high" | "immediate";
  explanation: string;
  created_at: string;
}

export async function getAlerts(status: string = "pending_review"): Promise<Alert[]> {
  const res = await fetch(`${API_BASE}/v1/safety/alerts?status_filter=${status}`, {
    headers: { ...authHeaders() }, credentials: "include",
  });
  if (res.status === 403) throw new Error("Not authorized — this account doesn't have reviewer access");
  if (!res.ok) throw new Error("Failed to load alerts");
  return res.json();
}

export async function acknowledgeAlert(alertId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/safety/alerts/${alertId}/acknowledge`, {
    method: "POST",
    headers: { ...authHeaders() }, credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to acknowledge alert");
}

export function saveToken(token: string) { accessToken = token; if (typeof window !== "undefined") sessionStorage.setItem("mb_access", token); }
export function clearToken() { accessToken = null; if (typeof window !== "undefined") sessionStorage.removeItem("mb_access"); }
export function hasToken(): boolean { return !!accessToken; }

// --- Journal ---
export interface JournalEntry {
  id: string;
  content: string;
  prompt_used: string | null;
  created_at: string;
}

export async function createJournal(content: string, promptUsed?: string): Promise<JournalEntry> {
  const res = await fetch(`${API_BASE}/v1/journals`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() }, credentials: "include",
    body: JSON.stringify({ content, prompt_used: promptUsed }),
  });
  if (!res.ok) throw new Error("Failed to save journal entry");
  return res.json();
}

export async function listJournals(): Promise<JournalEntry[]> {
  const res = await fetch(`${API_BASE}/v1/journals`, { headers: { ...authHeaders() }, credentials: "include" });
  if (!res.ok) throw new Error("Failed to load journal entries");
  return res.json();
}

// --- Mood history ---
export interface MoodEntry {
  id: string;
  mood_score: number;
  tags: string[];
  logged_at: string;
}

export async function listMoods(): Promise<MoodEntry[]> {
  const res = await fetch(`${API_BASE}/v1/mood`, { headers: { ...authHeaders() }, credentials: "include" });
  if (!res.ok) throw new Error("Failed to load mood history");
  return res.json();
}

// --- Privacy dashboard ---
export interface Preferences {
  long_term_memory_enabled: boolean;
  voice_emotion_enabled: boolean;
  wearable_integration_enabled: boolean;
  research_participation_opt_in: boolean;
  emergency_contacts_enabled: boolean;
}

export async function getPreferences(): Promise<Preferences> {
  const res = await fetch(`${API_BASE}/v1/privacy/preferences`, { headers: { ...authHeaders() }, credentials: "include" });
  if (!res.ok) throw new Error("Failed to load preferences");
  return res.json();
}

export async function updatePreferences(changes: Partial<Preferences>): Promise<Preferences> {
  const res = await fetch(`${API_BASE}/v1/privacy/preferences`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() }, credentials: "include",
    body: JSON.stringify(changes),
  });
  if (!res.ok) throw new Error("Failed to update preferences");
  return res.json();
}

export async function exportMyData(): Promise<any> {
  const res = await fetch(`${API_BASE}/v1/privacy/export`, { headers: { ...authHeaders() }, credentials: "include" });
  if (!res.ok) throw new Error("Failed to export data");
  return res.json();
}

export async function deleteAccount(password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/privacy/delete-account`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() }, credentials: "include",
    body: JSON.stringify({ password, confirmation: "DELETE MY ACCOUNT" }),
  });
  if (!res.ok) throw new Error("Failed to process deletion");
}

export interface ChatSummary { id:string; title:string|null; started_at:string; ended_at:string|null; message_count:number }
export interface ChatHistoryMessage { id:string; sender:"user"|"ai"; content:string; created_at:string }
export async function listChats():Promise<ChatSummary[]> { const r=await fetch(`${API_BASE}/v1/chats`,{headers:authHeaders(),credentials:"include"}); if(!r.ok) throw new Error("Failed to load chats"); return r.json(); }
export async function getChatMessages(id:string):Promise<ChatHistoryMessage[]> { const r=await fetch(`${API_BASE}/v1/chats/${id}/messages`,{headers:authHeaders(),credentials:"include"}); if(!r.ok) throw new Error("Failed to load conversation"); return r.json(); }
export async function renameChat(id:string,title:string){ const r=await fetch(`${API_BASE}/v1/chats/${id}?title=${encodeURIComponent(title)}`,{method:"PATCH",headers:authHeaders(),credentials:"include"}); if(!r.ok) throw new Error("Failed to rename chat"); }
export interface WeeklySummary { period_start:string; period_end:string; mood_average:number|null; mood_count:number; journal_count:number; chat_count:number; elevated_safety_events:number; highlights:string[] }
export async function getWeeklySummary():Promise<WeeklySummary>{const r=await fetch(`${API_BASE}/v1/summary/weekly`,{headers:authHeaders(),credentials:"include"});if(!r.ok)throw new Error("Failed to load summary");return r.json();}
export interface EmergencyContact { id:string; name:string; phone_masked:string; email_masked:string|null; relationship_label:string|null; consent_given_at:string|null; active:boolean }
export async function listEmergencyContacts():Promise<EmergencyContact[]>{const r=await fetch(`${API_BASE}/v1/emergency-contacts`,{headers:authHeaders(),credentials:"include"});if(!r.ok)throw new Error("Failed to load contacts");return r.json();}
export async function addEmergencyContact(data:{name:string;phone:string;email?:string;relationship_label?:string;consent:boolean}){const r=await fetch(`${API_BASE}/v1/emergency-contacts`,{method:"POST",headers:{"Content-Type":"application/json",...authHeaders()},body:JSON.stringify(data)});if(!r.ok){const d=await r.json().catch(()=>null);throw new Error(d?.detail||"Failed to add contact");}return r.json();}
export async function removeEmergencyContact(id:string){const r=await fetch(`${API_BASE}/v1/emergency-contacts/${id}`,{method:"DELETE",headers:authHeaders(),credentials:"include"});if(!r.ok)throw new Error("Failed to remove contact");}
export async function resolveAlert(id:string,notes:string=""){const r=await fetch(`${API_BASE}/v1/safety/alerts/${id}/resolve?notes=${encodeURIComponent(notes)}`,{method:"POST",headers:authHeaders(),credentials:"include"});if(!r.ok)throw new Error("Failed to resolve alert");}

export function saveRefreshToken(_token: string | null) { /* Refresh token is HttpOnly in staging/production. */ }
export function clearRefreshToken() { /* Cookie is cleared by /logout. */ }
export async function requestPasswordReset(email:string){ const r=await fetch(`${API_BASE}/v1/auth/password-reset/request`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email})}); if(!r.ok) throw new Error("Unable to request reset"); return r.json(); }
export async function verifyEmail(token:string){ const r=await fetch(`${API_BASE}/v1/auth/verify-email`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token})}); if(!r.ok) throw new Error("Verification failed"); return r.json(); }
export async function refreshAccessToken(): Promise<boolean> { const r=await fetch(`${API_BASE}/v1/auth/refresh`,{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify({refresh_token:"placeholder-refresh-body-not-used-in-cookie-mode"})}); if(!r.ok){clearToken();return false;} const data=await r.json();saveToken(data.access_token);return true; }
export async function logout(){ await fetch(`${API_BASE}/v1/auth/logout`,{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify({refresh_token:"placeholder-refresh-body-not-used-in-cookie-mode"})}).catch(()=>{}); clearToken(); }
