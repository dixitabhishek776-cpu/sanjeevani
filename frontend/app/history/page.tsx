"use client";
import {useEffect,useState} from "react";
import {listChats,getChatMessages,ChatSummary,ChatHistoryMessage} from "../../lib/api";
export default function HistoryPage(){const [chats,setChats]=useState<ChatSummary[]>([]);const [msgs,setMsgs]=useState<ChatHistoryMessage[]>([]);useEffect(()=>{listChats().then(setChats).catch(()=>{})},[]);return <main style={{maxWidth:760,margin:"0 auto",padding:24}}><h1>Conversation history</h1><div style={{display:"flex",gap:24}}><aside>{chats.map(c=><button key={c.id} onClick={()=>getChatMessages(c.id).then(setMsgs)} style={{display:"block",marginBottom:8}}>{c.title||"Conversation"} · {c.message_count}</button>)}</aside><section>{msgs.map(m=><p key={m.id}><b>{m.sender}:</b> {m.content}</p>)}</section></div><a href="/">Back to chat</a></main>}
