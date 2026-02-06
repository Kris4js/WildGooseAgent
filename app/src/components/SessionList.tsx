import { useState, useEffect } from "react";
import "./SessionList.css";

interface SessionListProps {
  currentSessionKey: string;
  onSessionSelect: (sessionKey: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionKey: string) => void;
}

interface SessionInfo {
  key: string;
  name: string;
}

const API_BASE = "http://127.0.0.1:8000";

export function SessionList({
  currentSessionKey,
  onSessionSelect,
  onNewSession,
  onDeleteSession,
}: SessionListProps) {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionSessionKey, setActionSessionKey] = useState<string | null>(null);
  const [actionName, setActionName] = useState("");

  const loadSessions = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/sessions`, {
        cache: "no-store",
      });
      if (response.ok) {
        const data = await response.json();
        // API now returns {sessions: [{key, name}, ...]}
        setSessions(data.sessions);
      }
    } catch (error) {
      console.error("Failed to load sessions:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const openActions = (sessionKey: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const session = sessions.find((s) => s.key === sessionKey);
    setActionSessionKey(sessionKey);
    setActionName(session?.name || sessionKey);
  };

  const closeActions = () => {
    setActionSessionKey(null);
    setActionName("");
  };

  const handleDelete = async () => {
    if (!actionSessionKey) return;

    try {
      const response = await fetch(
        `${API_BASE}/api/sessions/${encodeURIComponent(actionSessionKey)}`,
        { method: "DELETE" }
      );
      if (response.ok) {
        onDeleteSession(actionSessionKey);
        await loadSessions();
        closeActions();
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  const handleSaveName = async () => {
    if (!actionSessionKey) return;
    const nextName = actionName.trim();
    if (!nextName) return;

    try {
      const response = await fetch(
        `${API_BASE}/api/sessions/${encodeURIComponent(actionSessionKey)}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: nextName }),
        }
      );

      if (response.ok) {
        setSessions((prev) =>
          prev.map((s) =>
            s.key === actionSessionKey ? { ...s, name: nextName } : s
          )
        );
        closeActions();
      }
    } catch (error) {
      console.error("Failed to update session name:", error);
    }
  };

  return (
    <div className="session-list">
      <div className="session-list-header">
        <h3>会话历史</h3>
        <button className="new-session-btn" onClick={onNewSession}>
          + 新建会话
        </button>
      </div>

      <div className="session-list-content">
        {isLoading ? (
          <div className="session-list-loading">加载中...</div>
        ) : sessions.length === 0 ? (
          <div className="session-list-empty">暂无会话</div>
        ) : (
          <ul className="session-items">
            {sessions.map((session) => (
              <li
                key={session.key}
                className={`session-item ${
                  session.key === currentSessionKey ? "active" : ""
                }`}
                onClick={() => onSessionSelect(session.key)}
              >
                <span className="session-name">{session.name}</span>
                <button
                  className="session-actions-btn"
                  onClick={(e) => openActions(session.key, e)}
                  title="会话操作"
                >
                  …
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {actionSessionKey && (
        <div className="session-modal-backdrop" onClick={closeActions}>
          <div
            className="session-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="session-modal-header">会话操作</div>
            <div className="session-modal-body">
              <label className="session-modal-label">会话名称</label>
              <input
                type="text"
                className="session-modal-input"
                value={actionName}
                onChange={(e) => setActionName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleSaveName();
                  } else if (e.key === "Escape") {
                    e.preventDefault();
                    closeActions();
                  }
                }}
                autoFocus
              />
              <div className="session-modal-hint">
                删除后无法恢复，请谨慎操作。
              </div>
            </div>
            <div className="session-modal-actions">
              <button
                className="session-modal-btn"
                onClick={handleSaveName}
              >
                保存
              </button>
              <button
                className="session-modal-btn danger"
                onClick={handleDelete}
              >
                删除
              </button>
              <button className="session-modal-btn ghost" onClick={closeActions}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
