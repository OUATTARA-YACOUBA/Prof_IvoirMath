// ==================== ÉTAT GLOBAL ====================
let currentConversationId = null;
let currentLevel     = 'tout';
let currentLevelName = '📚 Tout le programme';
let conversations    = [];
let isAuthenticated  = false;
let isSending        = false;
let allCycles        = [];
let allClasses       = [];
let figureCounter    = 0;

// ==================== AUTHENTIFICATION ====================

async function checkAuthStatus() {
    try {
        const res  = await fetch('/api/auth/status');
        const data = await res.json();
        if (data.authenticated) {
            isAuthenticated = true;
            document.getElementById('usernameDisplay').textContent = data.username;
            showApp();
            await loadLevels();
            await loadConversations();
        } else { showAuth(); }
    } catch (e) { showAuth(); }
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

function showAuthError(msg) {
    const el = document.getElementById('authError');
    el.textContent = msg; el.style.display = 'block';
}
function hideAuthError() { document.getElementById('authError').style.display = 'none'; }

async function handleLogin(event) {
    event.preventDefault(); hideAuthError();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    try {
        const res  = await fetch('/api/auth/login', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        data.success ? await checkAuthStatus() : showAuthError(data.error || 'Identifiants incorrects.');
    } catch { showAuthError('Connexion impossible. Vérifiez votre réseau.'); }
}

async function handleRegister(event) {
    event.preventDefault(); hideAuthError();
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    try {
        const res  = await fetch('/api/auth/register', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        data.success ? await checkAuthStatus() : showAuthError(data.error || "Erreur lors de l'inscription.");
    } catch { showAuthError('Connexion impossible. Vérifiez votre réseau.'); }
}

async function handleLogout() {
    try {
        await fetch('/api/auth/logout', {method:'POST'});
        isAuthenticated = false; currentConversationId = null; conversations = [];
        showAuth();
    } catch(e) { console.error(e); }
}

// ==================== SÉLECTEUR DE NIVEAU ====================

async function loadLevels() {
    try {
        const res  = await fetch('/api/levels');
        const data = await res.json();
        allCycles  = data.cycles  || [];
        allClasses = data.classes || [];
        renderCycleSelector();
    } catch(e) { console.error(e); }
}

function renderCycleSelector() {
    const c = document.getElementById('cycleSelector');
    if (!c) return;
    c.innerHTML = allCycles.map(cy => `
        <button class="cycle-btn ${cy.id==='tout'?'active':''}"
                data-cycle="${cy.id}"
                onclick="onCycleClick('${cy.id}','${escapeHtml(cy.name)}')">
            ${cy.name}
        </button>`).join('');
    document.getElementById('classSelector').innerHTML = '';
    document.getElementById('classSelector').style.display = 'none';
}

function onCycleClick(cycleId, cycleName) {
    document.querySelectorAll('.cycle-btn').forEach(b =>
        b.classList.toggle('active', b.dataset.cycle === cycleId));
    if (cycleId === 'tout') {
        setActiveLevel('tout', cycleName);
        document.getElementById('classSelector').innerHTML = '';
        document.getElementById('classSelector').style.display = 'none';
        return;
    }
    const classes = allClasses.filter(c => c.cycle === cycleId);
    const cs = document.getElementById('classSelector');
    cs.style.display = 'flex';
    cs.innerHTML = `<span class="class-selector-label">Classe :</span>`
        + classes.map(c => `
        <button class="class-btn" data-class="${c.id}"
                onclick="onClassClick('${c.id}','${escapeHtml(c.name)}')">
            ${c.name}
        </button>`).join('');
}

function onClassClick(classId, className) {
    document.querySelectorAll('.class-btn').forEach(b =>
        b.classList.toggle('active', b.dataset.class === classId));
    setActiveLevel(classId, className);
}

function setActiveLevel(levelId, levelName) {
    currentLevel = levelId; currentLevelName = levelName;
    const badge = document.getElementById('currentLevelBadge');
    if (badge) badge.textContent = levelName;
    const ind = document.getElementById('sidebarLevelIndicator');
    if (ind) ind.textContent = levelName;
}

// ==================== CONVERSATIONS ====================

async function loadConversations() {
    try {
        const res  = await fetch('/api/conversations');
        const data = await res.json();
        conversations = data.conversations || [];
        renderConversationsList();
    } catch(e) { console.error(e); }
}

function getLevelLabel(id) {
    const c = allCycles.find(c=>c.id===id) || allClasses.find(c=>c.id===id);
    return c ? c.name : id;
}

function renderConversationsList() {
    const container = document.getElementById('conversationsList');
    if (conversations.length === 0) {
        container.innerHTML = '<div class="empty-conversations">Aucune conversation</div>';
        return;
    }
    container.innerHTML = conversations.map(conv => `
        <div class="conversation-item ${conv.id===currentConversationId?'active':''}"
             onclick="loadConversation('${conv.id}')">
            <div class="conv-header">
                <span class="conv-level-tag">${getLevelLabel(conv.level)}</span>
                <button class="conversation-delete"
                        onclick="event.stopPropagation();deleteConversation('${conv.id}')">🗑️</button>
            </div>
            <div class="conversation-title">${escapeHtml(conv.title)}</div>
        </div>`).join('');
}

async function createNewConversation() {
    try {
        const res  = await fetch('/api/conversations/new', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({level: currentLevel})
        });
        const data = await res.json();
        if (data.success) {
            currentConversationId = data.conversation_id;
            await loadConversations();
            showChatArea(); clearMessages(); addWelcomeMessage();
        }
    } catch(e) { alert('Impossible de créer une conversation. Réessayez.'); }
}

async function loadConversation(convId) {
    try {
        const res  = await fetch(`/api/conversations/${convId}`);
        const data = await res.json();
        if (data.conversation) {
            currentConversationId = convId;
            currentLevel     = data.conversation.level;
            currentLevelName = getLevelLabel(currentLevel);
            const badge = document.getElementById('currentLevelBadge');
            if (badge) badge.textContent = currentLevelName;
            renderConversationsList(); showChatArea(); clearMessages();
            data.messages.forEach(msg => addMessage(msg.content, msg.role==='user'));
        }
    } catch(e) { console.error(e); }
}

async function deleteConversation(convId) {
    if (!confirm('Supprimer cette conversation ?')) return;
    try {
        const res = await fetch(`/api/conversations/${convId}`, {method:'DELETE'});
        if (res.ok) {
            if (currentConversationId === convId) { currentConversationId=null; showWelcomeScreen(); }
            await loadConversations();
        }
    } catch(e) { console.error(e); }
}

// ==================== INTERFACE ====================

function showWelcomeScreen() {
    document.getElementById('welcomeScreen').style.display = 'flex';
    document.getElementById('chatArea').style.display      = 'none';
}
function showChatArea() {
    document.getElementById('welcomeScreen').style.display = 'none';
    document.getElementById('chatArea').style.display      = 'flex';
}
function clearMessages() { document.getElementById('chatMessages').innerHTML = ''; }

function addWelcomeMessage() {
    addMessage(
        'Bonjour ! 👋 Je suis **Prof IvoirMath**, votre assistant mathématiques.\n'
        + 'Niveau actif : **' + currentLevelName + '**\n'
        + 'Posez votre question de mathématiques !',
        false
    );
}

function addMessage(content, isUser) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user' : 'assistant'}`;
    div.innerHTML = `
        <div class="message-avatar">${isUser ? '👤' : '🎓'}</div>
        <div class="message-content">${formatMessage(content)}</div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    // Déclencher MathJax sur le nouveau message
    if (!isUser && window.MathJax) {
        MathJax.typesetPromise([div]).catch(() => {});
    }
}

// ==================== CONVERSION LATEX ====================
// Le modèle utilise parfois $...$ et $$...$$ (Markdown)
// On les convertit en \(...\) et \[...\] pour MathJax

function fixLatex(text) {
    // 1. Protéger les balises déjà correctes \(...\) et \[...\]
    const protected_zones = [];
    function protect(m) {
        protected_zones.push(m);
        return '\x00PROTECTED' + (protected_zones.length - 1) + '\x00';
    }

    // Protéger \[...\] et \(...\) existants
    text = text.replace(/\\\[[\s\S]*?\\\]/g, protect);
    text = text.replace(/\\\([\s\S]*?\\\)/g, protect);

    // 2. Convertir $$...$$ → \[...\]  (blocs centrés)
    text = text.replace(/\$\$([\s\S]*?)\$\$/g, function(_, inner) {
        return '\\[' + inner + '\\]';
    });

    // 3. Convertir $...$ → \(...\)  (inline)
    // Attention : ne pas capturer les $ isolés ou les prix
    text = text.replace(/\$([^\$\n]{1,200}?)\$/g, function(_, inner) {
        // Ignorer si ça ressemble à un prix (ex: $5, $20)
        if (/^\d+(\.\d+)?$/.test(inner.trim())) return '$' + inner + '$';
        return '\\(' + inner + '\\)';
    });

    // 4. Restaurer les zones protégées
    text = text.replace(/\x00PROTECTED(\d+)\x00/g, function(_, i) {
        return protected_zones[parseInt(i)];
    });

    return text;
}

// ==================== PARSER DE FIGURES ====================

function parseFigureTag(raw) {
    const obj = {};
    const pairs = raw.match(/(\w+)=([^\s]+)/g) || [];
    pairs.forEach(pair => {
        const eqIdx = pair.indexOf('=');
        const key   = pair.substring(0, eqIdx);
        const val   = pair.substring(eqIdx + 1);
        const num   = parseFloat(val);
        obj[key]    = (!isNaN(num) && val === String(num)) ? num : val;
    });
    if (obj.points && typeof obj.points === 'string') {
        const nums = obj.points.split(',').map(Number);
        const pts  = [];
        for (let i = 0; i < nums.length; i += 2) pts.push([nums[i], nums[i+1]]);
        obj.points = pts;
    }
    if (obj.labels && typeof obj.labels === 'string') {
        obj.labels = obj.labels.split(',');
    }
    return obj;
}

// ==================== RENDU JSXGraph ====================

function renderFigure(containerId, fig) {
    const el = document.getElementById(containerId);
    if (!el || typeof JXG === 'undefined') return;
    try {
        let bbox = [-7, 7, 7, -7];
        if (fig.type === 'square' && fig.side) {
            const s = fig.side / 2 + 1;
            bbox = [-(s+1), s+1, s+1, -(s+1)];
        } else if (fig.type === 'rectangle') {
            bbox = [-1, (fig.h||3) + 1, (fig.w||4) + 1, -1];
        } else if (fig.type === 'circle' && fig.r) {
            const r = fig.r + 1;
            bbox = [-r, r, r, -r];
        } else if (fig.type === 'segment') {
            const maxX = Math.max(Math.abs(fig.x1||0), Math.abs(fig.x2||5)) + 1;
            bbox = [-1, 2, maxX + 1, -2];
        }

        const board = JXG.JSXGraph.initBoard(containerId, {
            boundingbox: bbox, axis: true, grid: true,
            showCopyright: false, showNavigation: true,
        });

        const OG = '#FF7A00';

        if (fig.type === 'function') {
            try {
                // eslint-disable-next-line no-new-func
                const f = new Function('x', 'return ' + fig.expr + ';');
                board.create('functiongraph', [f, fig.xmin ?? -6, fig.xmax ?? 6], {
                    strokeColor: OG, strokeWidth: 2.5,
                    name: fig.label || '', withLabel: !!fig.label,
                });
            } catch(e) { console.warn('Erreur fonction:', fig.expr); }
        }
        else if (fig.type === 'square') {
            const cx = fig.cx||0, cy = fig.cy||0, s = (fig.side||4)/2;
            const pts = [
                board.create('point',[cx-s,cy-s],{name:'A',size:3,color:OG}),
                board.create('point',[cx+s,cy-s],{name:'B',size:3,color:OG}),
                board.create('point',[cx+s,cy+s],{name:'C',size:3,color:OG}),
                board.create('point',[cx-s,cy+s],{name:'D',size:3,color:OG}),
            ];
            board.create('polygon', pts, {fillColor:'rgba(255,122,0,0.1)',strokeColor:OG,strokeWidth:2});
            board.create('text',[cx, cy-s-0.4, fig.side ? fig.side+'cm' : ''],{color:OG,fontSize:14});
        }
        else if (fig.type === 'triangle') {
            const pts  = fig.points || [[0,0],[4,0],[2,3]];
            const lbls = fig.labels || ['A','B','C'];
            const jpts = pts.map((p,i) => board.create('point',p,{name:lbls[i]||'',size:3,color:OG}));
            board.create('polygon',jpts,{fillColor:'rgba(255,122,0,0.1)',strokeColor:OG,strokeWidth:2});
        }
        else if (fig.type === 'circle') {
            board.create('circle',[[fig.cx||0,fig.cy||0],fig.r||3],{
                strokeColor:OG,strokeWidth:2,fillColor:'rgba(255,122,0,0.08)'
            });
            board.create('point',[fig.cx||0,fig.cy||0],{name:'O',size:3,color:OG});
        }
        else if (fig.type === 'rectangle') {
            const x=fig.x||0, y=fig.y||0, w=fig.w||4, h=fig.h||3;
            const lbls = fig.labels||['A','B','C','D'];
            const pts = [
                board.create('point',[x,y],    {name:lbls[0],size:3,color:OG}),
                board.create('point',[x+w,y],  {name:lbls[1],size:3,color:OG}),
                board.create('point',[x+w,y+h],{name:lbls[2],size:3,color:OG}),
                board.create('point',[x,y+h],  {name:lbls[3],size:3,color:OG}),
            ];
            board.create('polygon',pts,{fillColor:'rgba(255,122,0,0.1)',strokeColor:OG,strokeWidth:2});
            board.create('text',[x+w/2,y-0.4,w+'cm'],  {color:OG,fontSize:13});
            board.create('text',[x+w+0.2,y+h/2,h+'cm'],{color:OG,fontSize:13});
        }
        else if (fig.type === 'segment') {
            const p1 = board.create('point',[fig.x1||0,fig.y1||0],{name:fig.labelA||'A',size:3,color:OG});
            const p2 = board.create('point',[fig.x2||5,fig.y2||0],{name:fig.labelB||'B',size:3,color:OG});
            board.create('segment',[p1,p2],{strokeColor:OG,strokeWidth:2.5});
            if (fig.label) {
                const mx = ((fig.x1||0)+(fig.x2||5))/2;
                const my = ((fig.y1||0)+(fig.y2||0))/2 + 0.4;
                board.create('text',[mx,my,fig.label],{color:OG,fontSize:13});
            }
        }
        else if (fig.type === 'line') {
            board.create('line',[[fig.x1||0,fig.y1||0],[fig.x2||4,fig.y2||4]],
                {strokeColor:OG,strokeWidth:2});
        }
    } catch(e) {
        console.error('Erreur JSXGraph:', e);
        const el2 = document.getElementById(containerId);
        if (el2) el2.innerHTML = '<p style="padding:1rem;color:#aaa;">Figure non disponible.</p>';
    }
}

// ==================== FORMATAGE DES MESSAGES ====================

function formatMessage(text) {
    text = String(text);

    // ── 1. Protéger les balises [FIGURE: ...] avant tout traitement ──
    const figures = [];
    text = text.replace(/\[FIGURE:\s*([^\]]+)\]/gi, function(_, raw) {
        figures.push(raw.trim());
        return '\x00FIGURE' + (figures.length - 1) + '\x00';
    });

    // ── 2. Convertir LaTeX Markdown → MathJax ──
    text = fixLatex(text);

    // ── 3. Markdown → HTML ──
    // Titres ### → gras avec séparateur
    text = text.replace(/^###\s+(.+)$/gm,
        '<div class="msg-section-title">$1</div>');

    // Titres ## → gras un peu plus grand
    text = text.replace(/^##\s+(.+)$/gm,
        '<div class="msg-title">$1</div>');

    // Séparateurs ---
    text = text.replace(/^---+$/gm,
        '<hr class="msg-divider">');

    // Listes numérotées : "1. texte"
    text = text.replace(/^(\d+)\.\s+(.+)$/gm,
        '<div class="msg-list-item"><span class="msg-list-num">$1.</span> $2</div>');

    // Listes à puces : "- texte" ou "* texte"
    text = text.replace(/^[-\*]\s+(.+)$/gm,
        '<div class="msg-bullet">• $1</div>');

    // Gras **...**
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italique *...*
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Code inline `...`
    text = text.replace(/`([^`]+)`/g, '<code class="msg-code">$1</code>');

    // Sauts de ligne
    text = text.replace(/\n/g, '<br>');

    // ── 4. Restaurer et rendre les figures ──
    text = text.replace(/\x00FIGURE(\d+)\x00/g, function(_, i) {
        const raw = figures[parseInt(i)];
        figureCounter++;
        const id  = 'fig_' + figureCounter;
        const fig = parseFigureTag(raw);
        if (!fig.type) return '';
        const lbl = fig.type === 'function' ? '📊 Graphique interactif' : '📐 Figure interactive';
        setTimeout(() => renderFigure(id, fig), 300);
        return `<div class="figure-container">
                    <div class="figure-label">${lbl}</div>
                    <div id="${id}" class="figure-frame"></div>
                </div>`;
    });

    return text;
}

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text; return d.innerHTML;
}

// ==================== ENVOI ====================

async function sendMessage() {
    if (!currentConversationId) {
        alert("Veuillez d'abord créer une nouvelle conversation.");
        return;
    }
    if (isSending) return;

    const input   = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const message = input.value.trim();
    if (!message) return;

    isSending = true;
    sendBtn.disabled    = true;
    sendBtn.textContent = '⏳';

    addMessage(message, true);
    input.value = ''; input.style.height = 'auto';
    showTypingIndicator();

    try {
        const response = await fetch(`/api/conversations/${currentConversationId}/message`, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({message})
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const reader  = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer    = '';
        let answered  = false;

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, {stream:true});
            const lines = buffer.split('\n');
            buffer = lines.pop();
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const jsonStr = line.slice(6).trim();
                if (!jsonStr) continue;
                try {
                    const chunk = JSON.parse(jsonStr);
                    if (chunk.error) {
                        hideTypingIndicator();
                        addMessage(chunk.error, false);
                        answered = true; break;
                    }
                    if (chunk.message) {
                        hideTypingIndicator();
                        addMessage(chunk.message, false);
                        answered = true;
                        await loadConversations();
                    }
                } catch { /* JSON partiel, ignorer */ }
            }
            if (answered) break;
        }

        if (!answered) {
            hideTypingIndicator();
            addMessage('Le service est momentanément indisponible. Veuillez réessayer.', false);
        }

    } catch(e) {
        console.error(e);
        hideTypingIndicator();
        addMessage('La connexion a été interrompue. Vérifiez votre réseau et réessayez.', false);
    } finally {
        isSending = false;
        sendBtn.disabled    = false;
        sendBtn.textContent = 'Envoyer';
        input.focus();
    }
}

function showTypingIndicator() {
    document.getElementById('typingIndicator').classList.add('active');
    const m = document.getElementById('chatMessages');
    if (m) m.scrollTop = m.scrollHeight;
}
function hideTypingIndicator() {
    document.getElementById('typingIndicator').classList.remove('active');
}

document.getElementById('userInput').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});
document.getElementById('userInput').addEventListener('keypress', function(e) {
    if (e.key==='Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

window.addEventListener('load', () => { checkAuthStatus(); });