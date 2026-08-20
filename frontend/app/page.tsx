import ChatWindow from "../components/ChatWindow";

export default function HomePage() {
  return (
    <main>
      <header style={{padding:"20px 24px",borderBottom:"1px solid #eee"}}>
        <strong>Sanjeevani</strong>
        <span style={{marginLeft:12,opacity:.7}}>AI mental-wellness companion</span>
      </header>
      <nav style={{padding:"12px 24px"}}><a href="/memory">Memory</a> · <a href="/privacy">Privacy</a> · <a href="/summary">Weekly summary</a></nav>
      <ChatWindow />
      <footer style={{padding:"24px",fontSize:13,opacity:.75}}>
        Sanjeevani is not a doctor or emergency service. In India, immediate danger: call 112.
        Tele-MANAS: 14416 / 1800-89-14416.
      </footer>
    </main>
  );
}
