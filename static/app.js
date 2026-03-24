// État global de l'application
let currentConversationId = null;
let currentLevel = 'tout';
let conversations = [];
let isAuthenticated = false;

// ==================== AUTHENTIFICATION ====================

async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        
        if (data.authenticated) {
            isAuthenticated = true;
            document.getElementById('usernameDisplay').textContent = data.username;
            showApp();
            await loadConversations();
        } else {
            showAuth();
        }
    } catch (error) {
        console.error('Erreur vérification auth:', error);
        showAuth();
    }
}

function showAuth() {
    document.getElementById('authScreen').style.display = 'flex';
    document.getElementById('appContainer').classList.remove('active');
}

function showApp() {
    document.getElementById('authScreen').style.display = 'none';
    document.getElementById('appContainer').classList.add('active');
}

function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
    
    if (tab === 'login') {
        document.querySelectorAll('.auth-tab')[0].classList.add('active');
        document.getElementById('loginForm').classList.add('active');
    } else {
        document.querySelectorAll('.auth-tab')[1].classList.add('active');
        document.getElementById('registerForm').classList.add('active');
    }
    
    hideAuthError();
}

function showAuthError(message) {
    const errorDiv = document.getElementById('authError');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideAuthError() {
    document.getElementById('authError').style.display = 'none';
}

async function handleLogin(event) {
    event.preventDefault();
    hideAuthError();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            await checkAuthStatus();
        } else {
            showAuthError(data.error || 'Erreur de connexion');
        }
    } catch (error) {
        showAuthError('Impossible de se connecter au serveur');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    hideAuthError();
    
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            await checkAuthStatus();
        } else {
            showAuthError(data.error || 'Erreur lors de l\'inscription');
        }
    } catch (error) {
        showAuthError('Impossible de se connecter au serveur');
    }
}

async function handleLogout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        isAuthenticated = false;
        currentConversationId = null;
        conversations = [];
        showAuth();
    } catch (error) {
        console.error('Erreur déconnexion:', error);
    }
}

// ==================== GESTION DES CONVERSATIONS ====================

async function loadConversations() {
    try {
        const response = await fetch('/api/conversations');
        const data = await response.json();
        
        conversations = data.conversations || [];
        renderConversationsList();
    } catch (error) {
        console.error('Erreur chargement conversations:', error);
    }
}

function renderConversationsList() {
    const container = document.getElementById('conversationsList');
    
    if (conversations.length === 0) {
        container.innerHTML = '<div class="empty-conversations">Aucune conversation</div>';
        return;
    }
    
    container.innerHTML = conversations.map(conv => `
        <div class="conversation-item ${conv.id === currentConversationId ? 'active' : ''}" 
             onclick="loadConversation('${conv.id}')">
            <div class="conversation-title">${escapeHtml(conv.title)}</div>
            <button class="conversation-delete" onclick="event.stopPropagation(); deleteConversation('${conv.id}')">
                🗑️
            </button>
        </div>
    `).join('');
}

async function createNewConversation() {
    try {
        const response = await fetch('/api/conversations/new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level: currentLevel })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentConversationId = data.conversation_id;
            await loadConversations();
            showChatArea();
            clearMessages();
            addWelcomeMessage();
        }
    } catch (error) {
        console.error('Erreur création conversation:', error);
        alert('Impossible de créer une nouvelle conversation');
    }
}

async function loadConversation(convId) {
    try {
        const response = await fetch(`/api/conversations/${convId}`);
        const data = await response.json();
        
        if (data.conversation) {
            currentConversationId = convId;
            currentLevel = data.conversation.level;
            
            // Mettre à jour le niveau sélectionné
            document.querySelectorAll('.level-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.level === currentLevel);
            });
            
            renderConversationsList();
            showChatArea();
            clearMessages();
            
            // Afficher les messages
            data.messages.forEach(msg => {
                addMessage(msg.content, msg.role === 'user');
            });
        }
    } catch (error) {
        console.error('Erreur chargement conversation:', error);
    }
}

async function deleteConversation(convId) {
    if (!confirm('Voulez-vous vraiment supprimer cette conversation ?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/conversations/${convId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            if (currentConversationId === convId) {
                currentConversationId = null;
                showWelcomeScreen();
            }
            await loadConversations();
        }
    } catch (error) {
        console.error('Erreur suppression:', error);
    }
}

function selectLevel(level) {
    currentLevel = level;
    document.querySelectorAll('.level-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.level === level);
    });
}

// ==================== INTERFACE CHAT ====================

function showWelcomeScreen() {
    document.getElementById('welcomeScreen').style.display = 'flex';
    document.getElementById('chatArea').style.display = 'none';
}

function showChatArea() {
    document.getElementById('welcomeScreen').style.display = 'none';
    document.getElementById('chatArea').style.display = 'flex';
}

function clearMessages() {
    document.getElementById('chatMessages').innerHTML = '';
}

function addWelcomeMessage() {
    addMessage('Bonjour ! Je suis votre professeur de mathématiques spécialisé dans le programme ivoirien. Posez-moi vos questions !', false);
}

function addMessage(content, isUser) {
    const messagesContainer = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${isUser ? '👤' : '🎓'}</div>
        <div class="message-content">${formatMessage(content)}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Rendre les formules LaTeX
    if (!isUser && window.MathJax) {
        MathJax.typesetPromise([messageDiv]).catch(err => console.error('Erreur MathJax:', err));
    }
}

function formatMessage(text) {
    text = String(text);
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    text = text.replace(/\n/g, '<br>');
    return text;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== ENVOI DE MESSAGES ====================

async function sendMessage() {
    if (!currentConversationId) {
        alert('Créez d\'abord une nouvelle conversation');
        return;
    }
    
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    
    addMessage(message, true);
    input.value = '';
    input.style.height = 'auto';
    
    showTypingIndicator();
    
    try {
        const response = await fetch(`/api/conversations/${currentConversationId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        
        hideTypingIndicator();
        
        const data = await response.json();
        
        if (data.success && data.message) {
            addMessage(data.message, false);
            await loadConversations(); // Rafraîchir pour mettre à jour le titre
        } else {
            addMessage('Erreur: Impossible de recevoir la réponse', false);
        }
    } catch (error) {
        hideTypingIndicator();
        console.error('Erreur envoi message:', error);
        addMessage('Erreur de connexion au serveur', false);
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

function showTypingIndicator() {
    document.getElementById('typingIndicator').classList.add('active');
}

function hideTypingIndicator() {
    document.getElementById('typingIndicator').classList.remove('active');
}

// ==================== EVENT LISTENERS ====================

document.getElementById('userInput').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

document.getElementById('userInput').addEventListener('keypress', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

// ==================== INITIALISATION ====================

window.addEventListener('load', () => {
    checkAuthStatus();
});