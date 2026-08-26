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

  /* ── Deal state ── */
  const [deals, setDeals] = useState([]);
  const [showDealForm, setShowDealForm] = useState(false);
  const [dealForm, setDealForm] = useState({
    waste_type: '', quantity: '', unit: 'tonnes', price_per_unit: '', direction: 'selling',
  });
  const [dealSubmitting, setDealSubmitting] = useState(false);
  const [confirmModal, setConfirmModal] = useState(null); // { action, dealId, title, message }

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
      const incoming = data.conversations || [];
      setConversations(prev => {
        if (JSON.stringify(prev) === JSON.stringify(incoming)) return prev;
        return incoming;
      });
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
      const incoming = data.messages || [];
      // Only update state if messages actually changed (avoids scroll-reset)
      setMessages(prev => {
        if (prev.length !== incoming.length) return incoming;
        if (prev.length === 0) return prev;
        if (prev[prev.length - 1]?.id !== incoming[incoming.length - 1]?.id) return incoming;
        return prev; // same data — keep old reference
      });
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  }, [activeConvId, currentUser]);

  /* ── fetch deals for active conversation ── */
  const loadDeals = useCallback(async () => {
    if (!activeConvId) return;
    try {
      const res = await fetch(`/api/deals/conversation/${activeConvId}`);
      const data = await res.json();
      const incoming = data.deals || [];
      setDeals(prev => {
        if (JSON.stringify(prev) === JSON.stringify(incoming)) return prev;
        return incoming;
      });
    } catch (err) {
      console.error('Failed to load deals:', err);
    }
  }, [activeConvId]);

  /* ── deal actions ── */
  const handleCreateDeal = async (e) => {
    e.preventDefault();
    if (!activeConvId || !activeConv || dealSubmitting) return;
    setDealSubmitting(true);
    try {
      const res = await fetch('/api/deals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: activeConvId,
          proposer_id: currentUser.id,
          responder_id: activeConv.partner_id,
          waste_type: dealForm.waste_type,
          quantity: parseFloat(dealForm.quantity) || 0,
          unit: dealForm.unit,
          price_per_unit: parseFloat(dealForm.price_per_unit) || 0,
          direction: dealForm.direction,
        }),
      });
      if (res.ok) {
        setShowDealForm(false);
        setDealForm({ waste_type: '', quantity: '', unit: 'tonnes', price_per_unit: '', direction: 'selling' });
        await loadDeals();
      }
    } catch (err) {
      console.error('Create deal failed:', err);
    } finally {
      setDealSubmitting(false);
    }
  };

  const handleDealAction = async (dealId, action) => {
    try {
      const res = await fetch(`/api/deals/${dealId}/${action}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: currentUser.id }),
      });
      if (res.ok) {
        await loadDeals();
        // Dashboard will pick up new stats on next load via analytics endpoint
      }
      setConfirmModal(null);
    } catch (err) {
      console.error(`Deal ${action} failed:`, err);
      setConfirmModal(null);
    }
  };

  const askConfirmation = (action, dealId, title, message) => {
    setConfirmModal({ action, dealId, title, message });
  };

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

  /* ── load messages + deals when active conv changes ── */
  useEffect(() => {
    if (activeConvId) {
      loadMessages();
      loadDeals();
      inputRef.current?.focus();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeConvId]);

  /* ── scroll only when new messages arrive ── */
  const prevMsgCount = useRef(0);
  useEffect(() => {
    if (messages.length > prevMsgCount.current) {
      scrollToBottom();
    }
    prevMsgCount.current = messages.length;
  }, [messages]);

  /* ── polling: refresh messages + deals every 3s (only when active) ── */
  useEffect(() => {
    pollRef.current = setInterval(() => {
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
      loadMessages();
      loadConversations();
      loadDeals();
    }, 3000);
    return () => clearInterval(pollRef.current);
  }, [loadMessages, loadConversations, loadDeals]);

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

  /* ── deal helpers ── */
  const statusEmoji = { active: '📋', completed: '🎉', cancelled: '🚫' };
  const statusLabel = { active: 'Active', completed: 'Completed', cancelled: 'Cancelled' };

  const activeDeals = deals.filter(d => d.status === 'active');
  const pastDeals = deals.filter(d => d.status === 'completed' || d.status === 'cancelled');

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
                  {c.partner_online && <span className="online-dot" title="Online now"></span>}
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
                {activeConv?.partner_online && <span className="online-dot" title="Online now"></span>}
              </div>
              <div className="chat-partner-info">
                <h3>{activeConv?.partner_name}</h3>
                <span>{activeConv?.partner_industry}{activeConv?.partner_online ? ' • 🟢 Online' : ''}</span>
              </div>
              {activeConv?.waste_context && (
                <span className="waste-tag">🏷️ {activeConv.waste_context}</span>
              )}
              <button className="deal-create-btn" onClick={() => setShowDealForm(true)} title="Create a deal proposal">
                📝 Create Deal
              </button>
            </div>

            {/* Active Deals Banner */}
            {activeDeals.length > 0 && (
              <div className="deals-banner">
                {activeDeals.map(deal => {
                  return (
                    <div key={deal.id} className={`deal-card deal-${deal.status}`}>
                      <div className="deal-card-header">
                        <span className="deal-status-badge">{statusEmoji[deal.status]} {statusLabel[deal.status]}</span>
                        <span className="deal-id">Deal #{deal.id}</span>
                      </div>
                      <div className="deal-card-body">
                        <div className="deal-info-grid">
                          <div className="deal-info-item">
                            <span className="deal-info-label">Waste Type</span>
                            <span className="deal-info-value">{deal.waste_type}</span>
                          </div>
                          <div className="deal-info-item">
                            <span className="deal-info-label">Quantity</span>
                            <span className="deal-info-value">{deal.quantity} {deal.unit}</span>
                          </div>
                          <div className="deal-info-item">
                            <span className="deal-info-label">Price/Unit</span>
                            <span className="deal-info-value">₹{Number(deal.price_per_unit).toLocaleString('en-IN')}</span>
                          </div>
                          <div className="deal-info-item">
                            <span className="deal-info-label">Total Value</span>
                            <span className="deal-info-value deal-total">₹{Number(deal.total_price).toLocaleString('en-IN')}</span>
                          </div>
                        </div>
                        <div className="deal-parties">
                          <span>{deal.proposer_name} → {deal.responder_name}</span>
                          <span className="deal-direction">{deal.direction === 'selling' ? '🏭 Selling' : '📥 Buying'}</span>
                        </div>
                      </div>
                      <div className="deal-card-actions">
                        {/* Either party can mark the deal as done */}
                        {deal.status === 'active' && (
                          <button
                            className="deal-btn deal-btn-complete"
                            onClick={() => askConfirmation('complete', deal.id,
                              '🎉 Complete This Deal?',
                              `This will mark the deal for ${deal.quantity} ${deal.unit} of ${deal.waste_type} (₹${Number(deal.total_price).toLocaleString('en-IN')}) as completed. Both parties' dashboards will be updated with the environmental impact. This action cannot be undone.`
                            )}
                          >
                            🎉 Mark Deal Done
                          </button>
                        )}
                        {/* Either party can cancel */}
                        {deal.status === 'active' && (
                          <button className="deal-btn deal-btn-cancel" onClick={() =>
                            askConfirmation('cancel', deal.id,
                              '🚫 Cancel This Deal?',
                              'Are you sure you want to cancel this deal? This action cannot be undone.'
                            )
                          }>
                            Cancel
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Past Deals (collapsed) */}
            {pastDeals.length > 0 && (
              <details className="past-deals-section">
                <summary className="past-deals-toggle">
                  📜 Past Deals ({pastDeals.length})
                </summary>
                <div className="past-deals-list">
                  {pastDeals.map(deal => (
                    <div key={deal.id} className={`deal-card-mini deal-${deal.status}`}>
                      <span className="deal-mini-status">{statusEmoji[deal.status]}</span>
                      <span className="deal-mini-type">{deal.waste_type}</span>
                      <span className="deal-mini-qty">{deal.quantity} {deal.unit}</span>
                      <span className="deal-mini-price">₹{Number(deal.total_price).toLocaleString('en-IN')}</span>
                      <span className={`deal-mini-badge status-${deal.status}`}>{statusLabel[deal.status]}</span>
                    </div>
                  ))}
                </div>
              </details>
            )}

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

      {/* ── Deal Form Modal ── */}
      {showDealForm && (
        <div className="modal-overlay" onClick={() => setShowDealForm(false)}>
          <div className="modal-content deal-form-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📝 Create Deal</h3>
              <button className="modal-close" onClick={() => setShowDealForm(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateDeal} className="deal-form">
              <p className="deal-form-subtitle">
                Create a formal deal with <strong>{activeConv?.partner_name}</strong>
              </p>

              <div className="deal-form-row">
                <label>Direction</label>
                <div className="deal-direction-toggle">
                  <button type="button"
                    className={`dir-btn ${dealForm.direction === 'selling' ? 'active' : ''}`}
                    onClick={() => setDealForm(f => ({ ...f, direction: 'selling' }))}
                  >🏭 I'm Selling</button>
                  <button type="button"
                    className={`dir-btn ${dealForm.direction === 'buying' ? 'active' : ''}`}
                    onClick={() => setDealForm(f => ({ ...f, direction: 'buying' }))}
                  >📥 I'm Buying</button>
                </div>
              </div>

              <div className="deal-form-row">
                <label>Waste Type *</label>
                <input
                  type="text"
                  placeholder="e.g. Metal, Plastic, Glass…"
                  value={dealForm.waste_type}
                  onChange={e => setDealForm(f => ({ ...f, waste_type: e.target.value }))}
                  required
                />
              </div>

              <div className="deal-form-row-group">
                <div className="deal-form-row">
                  <label>Quantity *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    value={dealForm.quantity}
                    onChange={e => setDealForm(f => ({ ...f, quantity: e.target.value }))}
                    required
                  />
                </div>
                <div className="deal-form-row">
                  <label>Unit</label>
                  <select value={dealForm.unit} onChange={e => setDealForm(f => ({ ...f, unit: e.target.value }))}>
                    <option value="tonnes">Tonnes</option>
                    <option value="kg">Kilograms</option>
                    <option value="litres">Litres</option>
                    <option value="units">Units</option>
                  </select>
                </div>
                <div className="deal-form-row">
                  <label>Price per Unit (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    value={dealForm.price_per_unit}
                    onChange={e => setDealForm(f => ({ ...f, price_per_unit: e.target.value }))}
                    required
                  />
                </div>
              </div>

              {dealForm.quantity && dealForm.price_per_unit && (
                <div className="deal-form-total">
                  <span>Total Value:</span>
                  <strong>₹{(parseFloat(dealForm.quantity || 0) * parseFloat(dealForm.price_per_unit || 0)).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong>
                </div>
              )}

              <div className="deal-form-actions">
                <button type="button" className="deal-btn deal-btn-cancel" onClick={() => setShowDealForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="deal-btn deal-btn-submit" disabled={dealSubmitting}>
                  {dealSubmitting ? '⏳ Creating…' : '📤 Create Deal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Confirmation Modal ── */}
      {confirmModal && (
        <div className="modal-overlay" onClick={() => setConfirmModal(null)}>
          <div className="modal-content confirm-modal" onClick={e => e.stopPropagation()}>
            <h3>{confirmModal.title}</h3>
            <p>{confirmModal.message}</p>
            <div className="confirm-actions">
              <button className="deal-btn deal-btn-cancel" onClick={() => setConfirmModal(null)}>
                No, Go Back
              </button>
              <button
                className={`deal-btn ${confirmModal.action === 'complete' ? 'deal-btn-complete' : 'deal-btn-reject'}`}
                onClick={() => handleDealAction(confirmModal.dealId, confirmModal.action)}
              >
                {confirmModal.action === 'complete' ? '🎉 Yes, Complete Deal' : '🚫 Yes, Cancel Deal'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;
