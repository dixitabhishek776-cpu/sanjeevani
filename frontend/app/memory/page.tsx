"use client";
import {useEffect,useState} from "react";
import {api} from "../../lib/api";
export default function MemoryPage(){
 const [items,setItems]=useState<any[]>([]),[content,setContent]=useState(""),[enabled,setEnabled]=useState(false),[busy,setBusy]=useState(false);
 async function load(){try{const p=await api("/v1/privacy/preferences");setEnabled(!!p.long_term_memory_enabled);if(p.long_term_memory_enabled)setItems(await api("/v1/memories"));}catch{}}
 useEffect(()=>{load()},[]);
 async function save(){if(!content.trim())return;setBusy(true);try{await api("/v1/memories",{method:"POST",body:JSON.stringify({content:content.trim(),category:"preference"})});setContent("");await load();}finally{setBusy(false)}}
 async function remove(id:string){await api(`/v1/memories/${id}`,{method:"DELETE"});await load()}
 return <main style={{maxWidth:800,margin:"40px auto",padding:20}}><h1>What Sanjeevani remembers</h1><p>Memory is optional. Only information you deliberately save is stored here.</p>{!enabled?<div style={{padding:16,border:"1px solid #ddd",borderRadius:12}}>Long-term memory is disabled. Enable it in Privacy settings before adding memories.</div>:<><textarea value={content} onChange={e=>setContent(e.target.value)} placeholder="Example: I prefer short check-ins in the evening." rows={4} style={{width:"100%",padding:12}}/><button onClick={save} disabled={busy} style={{marginTop:10,padding:"10px 16px"}}>Save memory</button><section style={{marginTop:28}}>{items.map(x=><article key={x.id} style={{padding:14,border:"1px solid #eee",borderRadius:12,marginBottom:10}}><div>{x.content}</div><small>{x.category}</small><br/><button onClick={()=>remove(x.id)}>Delete</button></article>)}</section></>}</main>
}
