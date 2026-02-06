import { useState } from "react";
import { Chat } from "./pages/Chat";
import { Resources } from "./pages/Resources";
import "./App.css";

type Page = "chat" | "resources";

function App() {
  const [page, setPage] = useState<Page>("chat");

  return (
    <div className="app">
      <nav className="app-nav">
        <div className="app-title">Wild Goose Agent</div>
        <div className="app-tabs">
          <button
            className={`app-tab ${page === "chat" ? "active" : ""}`}
            onClick={() => setPage("chat")}
          >
            💬 对话
          </button>
          <button
            className={`app-tab ${page === "resources" ? "active" : ""}`}
            onClick={() => setPage("resources")}
          >
            📦 资源
          </button>
        </div>
      </nav>
      <main className="app-main">
        {page === "chat" && <Chat />}
        {page === "resources" && <Resources />}
      </main>
    </div>
  );
}

export default App;
