import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import './Chat.css';

const Chat = () => {
  const [searchParams] = useSearchParams();
  const withUserId = searchParams.get('with');
  const wasteCtx = searchParams.get('waste') || '';

  const currentUser = useMemo(() => {
    try { return JSON.parse(localStorage.getItem('user') || 'null'); }
    catch { return null; }
  }, []);

  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef(null);
  const pollRef = useRef(null);
  const inputRef = useRef(null);

  /* ── helpers ── */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const activeConv = conversations.find(c => c.id === activeConvId);

  /* ── fetch conversation list ── */
  const loadConversations = useCallback(async () => {
    if (!currentUser?.id) return;
    try {
      const res = await fetch(`/api/chat/conversations?user_id=${currentUser.id}`);
      const data = await res.json();
      setConversations(data.conversations || []);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  }, [currentUser]);

  /* ── fetch messages for active conversation ── */
  const loadMessages = useCallback(async () => {
    if (!activeConvId || !currentUser?.id) return;
    try {
      const res = await fetch(`/api/chat/messages/${activeConvId}?user_id=${currentUser.id}`);
      const data = await res.json();
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  }, [activeConvId, currentUser]);

  /* ── initial load + auto-open conversation from ?with= param ── */
  useEffect(() => {
    const init = async () => {
      await loadConversations();
      if (withUserId && currentUser?.id) {
        try {
          const res = await fetch('/api/chat/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: currentUser.id,
              other_id: Number(withUserId),
              waste_context: wasteCtx,
            }),
          });
          const data = await res.json();
          if (data.conversation) {
            setActiveConvId(data.conversation.id);
            await loadConversations();      // refresh list
          }
        } catch (e) {
          console.error('Auto-start conversation failed:', e);
        }
      }
    };
    init();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ── load messages when active conv changes ── */
  useEffect(() => {
    if (activeConvId) {
      loadMessages();
      inputRef.current?.focus();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeConvId]);

  /* ── scroll when messages update ── */
  useEffect(() => { scrollToBottom(); }, [messages]);

  /* ── polling: refresh messages every 3s ── */
  useEffect(() => {
    pollRef.current = setInterval(() => {
      loadMessages();
      loadConversations();
    }, 3000);
    return () => clearInterval(pollRef.current);
  }, [loadMessages, loadConversations]);

  /* ── send message ── */
  const handleSend = async (e) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || !activeConvId || sending) return;
    setSending(true);
    try {
      const res = await fetch(`/api/chat/messages/${activeConvId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender_id: currentUser.id, content: text }),
      });
      if (res.ok) {
        setDraft('');
        await loadMessages();
        await loadConversations();
      }
    } catch (err) {
      console.error('Send failed:', err);
    } finally {
      setSending(false);
    }
  };

  const formatTime = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    if (isToday) return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) + ' ' +
           d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  };

  if (!currentUser) {
    return (
      <div className="chat-page">
        <div className="chat-empty-full">
          <span className="empty-icon">🔒</span>
          <h2>Please log in to use chat</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-page">
      {/* Sidebar: conversation list */}
      <aside className={`chat-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>💬 Chats</h2>
          <button className="sidebar-close" onClick={() => setSidebarOpen(false)}>✕</button>
        </div>

        {conversations.length === 0 ? (
          <div className="no-convos">
            <p>No conversations yet</p>
            <span>Start chatting from the <strong>Matches</strong> page!</span>
          </div>
        ) : (
          <div className="convo-list">
            {conversations.map((c) => (
              <button
                key={c.id}
                className={`convo-item ${c.id === activeConvId ? 'active' : ''}`}
                onClick={() => { setActiveConvId(c.id); setSidebarOpen(false); }}
              >
                <div className="convo-avatar">
                  {(c.partner_name || '?')[0].toUpperCase()}
                </div>
                <div className="convo-meta">
                  <span className="convo-name">{c.partner_name}</span>
                  <span className="convo-industry">{c.partner_industry}</span>
                  <span className="convo-last">{c.last_message ? c.last_message.slice(0, 40) + (c.last_message.length > 40 ? '…' : '') : 'No messages yet'}</span>
                </div>
                <div className="convo-right">
                  <span className="convo-time">{formatTime(c.last_message_at)}</span>
                  {c.unread_count > 0 && <span className="unread-badge">{c.unread_count}</span>}
                </div>
              </button>
            ))}
          </div>
        )}
      </aside>

      {/* Main chat area */}
      <main className="chat-main">
        {!activeConvId ? (
          <div className="chat-empty-full">
            <span className="empty-icon">💬</span>
            <h2>Select a conversation</h2>
            <p>Pick a chat from the sidebar or start one from the Matches page</p>
            <button className="sidebar-toggle-btn" onClick={() => setSidebarOpen(true)}>
              Open Chats
            </button>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="chat-header">
              <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>☰</button>
              <div className="chat-partner-avatar">
                {(activeConv?.partner_name || '?')[0].toUpperCase()}
              </div>
              <div className="chat-partner-info">
                <h3>{activeConv?.partner_name}</h3>
                <span>{activeConv?.partner_industry}</span>
              </div>
              {activeConv?.waste_context && (
                <span className="waste-tag">🏷️ {activeConv.waste_context}</span>
              )}
            </div>

            {/* Messages */}
            <div className="chat-messages">
              {messages.length === 0 ? (
                <div className="msg-empty">
                  <p>👋 Start the conversation! Discuss logistics, pricing, or waste details.</p>
                </div>
              ) : (
                messages.map((m) => {
                  const isMe = m.sender_id === currentUser.id;
                  return (
                    <div key={m.id} className={`msg-row ${isMe ? 'me' : 'them'}`}>
                      {!isMe && <div className="msg-avatar">{(m.sender_name || '?')[0].toUpperCase()}</div>}
                      <div className={`msg-bubble ${isMe ? 'mine' : 'theirs'}`}>
                        <p>{m.content}</p>
                        <span className="msg-time">{formatTime(m.created_at)}</span>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form className="chat-input-bar" onSubmit={handleSend}>
              <input
                ref={inputRef}
                type="text"
                placeholder="Type a message…"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                disabled={sending}
              />
              <button type="submit" disabled={!draft.trim() || sending} className="send-btn">
                {sending ? '⏳' : '➤'}
              </button>
            </form>
          </>
        )}
      </main>
    </div>
  );
};

export default Chat;
