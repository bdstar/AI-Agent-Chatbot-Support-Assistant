/* ═══════════════════════════════════════════════
   LIFE INSURANCE AI AGENT — Frontend Logic
   ═══════════════════════════════════════════════ */

// ─── State ───
let currentSessionId = null;
let isLoading = false;

// ─── DOM Elements ───
const chatInput = document.getElementById('chatInput');
const btnSend = document.getElementById('btnSend');
const chatMessages = document.getElementById('chatMessages');
const welcomeScreen = document.getElementById('welcomeScreen');
const sessionsList = document.getElementById('sessionsList');
const sessionsEmpty = document.getElementById('sessionsEmpty');
const searchInput = document.getElementById('searchInput');
const btnNewChat = document.getElementById('btnNewChat');
const btnIngest = document.getElementById('btnIngest');
const btnDeleteSession = document.getElementById('btnDeleteSession');
const referencesContent = document.getElementById('referencesContent');
const referencesEmpty = document.getElementById('referencesEmpty');
const loadingOverlay = document.getElementById('loadingOverlay');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const sidebar = document.getElementById('sidebar');
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const btnToggleRefs = document.getElementById('btnToggleRefs');
const referencesPanel = document.getElementById('referencesPanel');


// ─── Initialization ───
document.addEventListener('DOMContentLoaded', () => {
    loadSessions();
    checkDocumentStatus();
    setupEventListeners();
    createNewChat();
});


// ─── Event Listeners ───
function setupEventListeners() {
    // Send message
    btnSend.addEventListener('click', sendMessage);

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        btnSend.disabled = !chatInput.value.trim();
    });

    // New chat
    btnNewChat.addEventListener('click', createNewChat);

    // Ingest documents
    btnIngest.addEventListener('click', ingestDocuments);

    // Delete session
    btnDeleteSession.addEventListener('click', deleteCurrentSession);

    // Search
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const query = searchInput.value.trim();
            if (query) {
                searchSessions(query);
            } else {
                loadSessions();
            }
        }, 300);
    });

    // Mobile sidebar toggle
    mobileMenuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    // Toggle references panel
    btnToggleRefs.addEventListener('click', () => {
        referencesPanel.classList.toggle('collapsed');
    });

    // Close sidebar on overlay click (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 900 && sidebar.classList.contains('open')) {
            if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        }
    });
}


// ═══════════════════════════════════════════════
// Chat Functions
// ═══════════════════════════════════════════════

function createNewChat() {
    currentSessionId = generateUUID();
    clearChat();
    btnDeleteSession.style.display = 'none';
    clearReferences();

    // Close mobile sidebar
    sidebar.classList.remove('open');

    // Deselect all sessions
    document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));

    chatInput.focus();
}


async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isLoading) return;

    // Hide welcome screen
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }

    // Display user message
    appendMessage('user', message);

    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    btnSend.disabled = true;

    // Show typing indicator
    const typingEl = showTypingIndicator();

    isLoading = true;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message,
            }),
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to get response');
        }

        const data = await response.json();

        // Remove typing indicator
        typingEl.remove();

        // Display AI response
        appendMessage('ai', data.response);

        // Update references panel
        if (data.references && data.references.length > 0) {
            displayReferences(data.references);
        }

        // Show delete button
        btnDeleteSession.style.display = '';

        // Refresh sessions list
        loadSessions();

    } catch (error) {
        typingEl.remove();
        appendMessage('ai', `⚠️ Error: ${error.message}. Please try again.`);
        showToast(error.message, 'error');
    } finally {
        isLoading = false;
    }
}


function appendMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;

    const avatarLabel = role === 'user' ? 'You' : 'AI';
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Format AI messages (basic markdown-like formatting)
    let formattedContent = content;
    if (role === 'ai') {
        formattedContent = formatAIResponse(content);
    } else {
        formattedContent = escapeHtml(content);
    }

    msgDiv.innerHTML = `
        <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div>
            <div class="message-content">${formattedContent}</div>
            <div class="message-time">${timeStr}</div>
        </div>
    `;

    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}


function formatAIResponse(text) {
    // Escape HTML first
    let formatted = escapeHtml(text);

    // Bold: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic: *text*
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Line breaks
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = formatted.replace(/\n/g, '<br>');

    // Wrap in paragraphs
    formatted = '<p>' + formatted + '</p>';

    return formatted;
}


function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
    return typingDiv;
}


function clearChat() {
    chatMessages.innerHTML = '';

    // Re-add welcome screen
    const welcomeHtml = `
        <div class="welcome-screen" id="welcomeScreen">
            <div class="welcome-icon">
                <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="url(#welcomeGrad)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <defs>
                        <linearGradient id="welcomeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#6366f1"/>
                            <stop offset="100%" stop-color="#a855f7"/>
                        </linearGradient>
                    </defs>
                    <path d="M12 2a10 10 0 0 1 10 10c0 6-10 12-10 12S2 18 2 12A10 10 0 0 1 12 2z"/>
                    <path d="M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0"/>
                </svg>
            </div>
            <h1 class="welcome-title">Life Insurance AI Assistant</h1>
            <p class="welcome-subtitle">Ask me anything about life insurance policies, claims, benefits, and more. I'll provide accurate answers backed by document references.</p>
            <div class="suggestion-chips">
                <button class="chip" onclick="sendSuggestion(this)">What is term life insurance?</button>
                <button class="chip" onclick="sendSuggestion(this)">How do I file a claim?</button>
                <button class="chip" onclick="sendSuggestion(this)">What factors affect premiums?</button>
                <button class="chip" onclick="sendSuggestion(this)">Difference between whole and term life?</button>
            </div>
        </div>
    `;
    chatMessages.innerHTML = welcomeHtml;
}


function scrollToBottom() {
    requestAnimationFrame(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}


// ═══════════════════════════════════════════════
// Session Functions
// ═══════════════════════════════════════════════

async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        if (!response.ok) throw new Error('Failed to load sessions');
        const sessions = await response.json();

        renderSessions(sessions);
    } catch (error) {
        console.error('Error loading sessions:', error);
    }
}


function renderSessions(sessions) {
    // Clear existing items but keep the empty state element
    const existingItems = sessionsList.querySelectorAll('.session-item');
    existingItems.forEach(el => el.remove());

    if (sessions.length === 0) {
        sessionsEmpty.style.display = 'flex';
        return;
    }

    sessionsEmpty.style.display = 'none';

    sessions.forEach(session => {
        const item = document.createElement('div');
        item.className = `session-item${session.session_id === currentSessionId ? ' active' : ''}`;
        item.dataset.sessionId = session.session_id;

        const title = session.first_message || 'New Chat';
        const timeAgo = formatTimeAgo(new Date(session.created_at));

        item.innerHTML = `
            <div class="session-title" title="${escapeHtml(title)}">${escapeHtml(truncate(title, 40))}</div>
            <div class="session-meta">
                <span>${timeAgo}</span>
                <span>·</span>
                <span>${session.message_count} msg${session.message_count !== 1 ? 's' : ''}</span>
            </div>
            <button class="btn-icon session-delete" title="Delete session" onclick="event.stopPropagation(); deleteSession('${session.session_id}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        `;

        item.addEventListener('click', () => loadSession(session.session_id));
        sessionsList.insertBefore(item, sessionsEmpty);
    });
}


async function loadSession(sessionId) {
    if (isLoading) return;

    currentSessionId = sessionId;

    // Close mobile sidebar
    sidebar.classList.remove('open');

    // Highlight active session
    document.querySelectorAll('.session-item').forEach(el => {
        el.classList.toggle('active', el.dataset.sessionId === sessionId);
    });

    // Clear chat
    chatMessages.innerHTML = '';
    clearReferences();

    try {
        const response = await fetch(`/api/sessions/${sessionId}`);
        if (!response.ok) throw new Error('Failed to load session');
        const history = await response.json();

        if (history.length === 0) {
            clearChat();
            return;
        }

        // Display all messages
        let lastReferences = [];
        history.forEach(item => {
            appendMessage('user', item.user_message);
            appendMessage('ai', item.ai_response);
            if (item.references && item.references.length > 0) {
                lastReferences = item.references;
            }
        });

        // Show references from the last exchange
        if (lastReferences.length > 0) {
            displayReferences(lastReferences);
        }

        btnDeleteSession.style.display = '';
        scrollToBottom();

    } catch (error) {
        showToast('Failed to load conversation', 'error');
        console.error('Error loading session:', error);
    }
}


async function searchSessions(query) {
    try {
        const response = await fetch(`/api/sessions/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Search failed');
        const results = await response.json();

        // Convert search results to session format for rendering
        const sessions = results.map(r => ({
            session_id: r.session_id,
            first_message: r.message_preview,
            message_count: 0,
            created_at: r.created_at,
        }));

        renderSessions(sessions);
    } catch (error) {
        console.error('Error searching sessions:', error);
    }
}


async function deleteSession(sessionId) {
    if (!confirm('Delete this conversation?')) return;

    try {
        const response = await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete');

        showToast('Conversation deleted', 'success');

        if (sessionId === currentSessionId) {
            createNewChat();
        }
        loadSessions();

    } catch (error) {
        showToast('Failed to delete conversation', 'error');
    }
}


function deleteCurrentSession() {
    if (currentSessionId) {
        deleteSession(currentSessionId);
    }
}


// ═══════════════════════════════════════════════
// References Functions
// ═══════════════════════════════════════════════

function displayReferences(references) {
    // Remove empty state
    referencesEmpty.style.display = 'none';

    // Clear previous reference cards
    const existingCards = referencesContent.querySelectorAll('.reference-card');
    existingCards.forEach(el => el.remove());

    references.forEach((ref, index) => {
        const card = document.createElement('div');
        card.className = 'reference-card';
        card.style.animationDelay = `${index * 0.1}s`;

        const pageInfo = ref.page ? `<div class="ref-page">📄 Page ${ref.page}</div>` : '';

        card.innerHTML = `
            <div class="ref-source">
                <span class="ref-source-number">${index + 1}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                </svg>
                <span>${escapeHtml(ref.source || 'Unknown')}</span>
            </div>
            <div class="ref-text">${escapeHtml(truncate(ref.content || '', 300))}</div>
            ${pageInfo}
        `;

        referencesContent.appendChild(card);
    });
}


function clearReferences() {
    const existingCards = referencesContent.querySelectorAll('.reference-card');
    existingCards.forEach(el => el.remove());
    referencesEmpty.style.display = 'flex';
}


// ═══════════════════════════════════════════════
// Document Ingestion
// ═══════════════════════════════════════════════

async function ingestDocuments() {
    if (btnIngest.disabled) return;

    btnIngest.disabled = true;
    loadingOverlay.style.display = 'flex';

    try {
        const response = await fetch('/api/documents/ingest', { method: 'POST' });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Ingestion failed');
        }

        const data = await response.json();
        showToast(data.message, data.status === 'success' ? 'success' : 'warning');
        checkDocumentStatus();

    } catch (error) {
        showToast(`Ingestion failed: ${error.message}`, 'error');
    } finally {
        btnIngest.disabled = false;
        loadingOverlay.style.display = 'none';
    }
}


async function checkDocumentStatus() {
    try {
        const response = await fetch('/api/documents/status');
        if (!response.ok) throw new Error('Status check failed');
        const data = await response.json();

        statusDot.className = `status-dot ${data.status}`;
        statusText.textContent = data.status === 'ready'
            ? `${data.total_chunks} chunks ready`
            : 'No documents ingested';

    } catch (error) {
        statusDot.className = 'status-dot';
        statusText.textContent = 'Status unavailable';
    }
}


// ═══════════════════════════════════════════════
// Suggestion Chips
// ═══════════════════════════════════════════════

function sendSuggestion(chipEl) {
    chatInput.value = chipEl.textContent;
    btnSend.disabled = false;
    sendMessage();
}


// ═══════════════════════════════════════════════
// Utility Functions
// ═══════════════════════════════════════════════

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}


function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


function truncate(text, maxLen) {
    if (!text) return '';
    return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
}


function formatTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHr = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHr / 24);

    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHr < 24) return `${diffHr}h ago`;
    if (diffDay === 1) return 'Yesterday';
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}


function showToast(message, type = 'success') {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(el => el.remove());

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3500);
}
