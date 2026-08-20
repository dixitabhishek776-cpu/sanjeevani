"use client";
import {useEffect,useState} from "react";
import {getWeeklySummary,WeeklySummary} from "../../lib/api";
export default function SummaryPage(){const [s,setS]=useState<WeeklySummary|null>(null);const [e,setE]=useState("");useEffect(()=>{getWeeklySummary().then(setS).catch(x=>setE(x.message))},[]);return <main style={{maxWidth:640,margin:"0 auto",padding:24}}><h1>Weekly wellbeing summary 🌱</h1>{e&&<p>{e}</p>}{s&&<><p>Average mood: <b>{s.mood_average??"—"}/10</b></p><p>{s.mood_count} mood logs · {s.journal_count} journal entries · {s.chat_count} chats</p><ul>{s.highlights.map((h,i)=><li key={i}>{h}</li>)}</ul></>}<a href="/">Back to chat</a></main>}
