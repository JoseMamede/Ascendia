let isRegistering = false;

function toggleAuthMode() {
    isRegistering = !isRegistering;
    document.getElementById('auth-title').innerText = isRegistering ? 'Cadastrar no LifeQuest' : 'Entrar no LifeQuest';
    document.getElementById('auth-btn').innerText = isRegistering ? 'Cadastrar' : 'Entrar';
    document.getElementById('toggle-auth').innerText = isRegistering ? 'Já tem uma conta? Entre' : 'Não tem uma conta? Cadastre-se';
    document.getElementById('email-group').style.display = isRegistering ? 'block' : 'none';
}

async function handleAuth(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const email = document.getElementById('email').value;

    const url = isRegistering ? '/api/register' : '/api/login';
    const payload = isRegistering ? { username, email, password } : { username, password };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        
        if (!response.ok) throw new Error(data.error);

        if (isRegistering) {
            alert('Cadastro realizado com sucesso! Faça login.');
            toggleAuthMode();
        } else {
            document.getElementById('auth-section').style.display = 'none';
            document.getElementById('main-nav').style.display = 'block';
            document.getElementById('game-section').style.display = 'block';
            loadProfile();
        }
    } catch (error) {
        const alertBox = document.getElementById('auth-alert');
        alertBox.innerText = error.message;
        alertBox.classList.remove('d-none');
    }
}

function showSection(sectionId) {
    document.querySelectorAll('.game-panel').forEach(p => p.style.display = 'none');
    document.getElementById(sectionId).style.display = 'block';

    document.querySelectorAll('.navbar-nav .nav-link').forEach(l => l.classList.remove('active'));
    event.target.classList.add('active');

    if (sectionId === 'profile-section') loadProfile();
    if (sectionId === 'quests-section') loadQuests();
    if (sectionId === 'shop-section') loadShop();
    if (sectionId === 'guild-section') loadGuildAndBoss();
}

async function loadProfile() {
    try {
        const res = await fetch('/api/profile');
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);

        const charInfo = document.getElementById('character-info');
        const createContainer = document.getElementById('create-char-container');

        if (data.character) {
            createContainer.style.display = 'none';
            charInfo.innerHTML = `
                <p><strong>Nome:</strong> ${data.character.name}</p>
                <p><strong>Classe:</strong> ${data.character.class_name}</p>
                <p><strong>Nível:</strong> ${data.character.level}</p>
                <p><strong>XP:</strong> ${data.character.experience} / ${data.character.next_level_xp}</p>
                <p><strong>Moedas:</strong> 🪙 ${data.character.coins}</p>
            `;
            loadInventory();
        } else {
            createContainer.style.display = 'block';
            charInfo.innerHTML = '<p class="text-warning">Você ainda não criou seu personagem!</p>';
            loadClasses();
        }
    } catch (error) {
        console.error(error);
    }
}

async function loadClasses() {
    const res = await fetch('/api/classes');
    const classes = await res.json();
    const select = document.getElementById('char-class');
    select.innerHTML = classes.map(c => `<option value="${c.id}">${c.name} - ${c.description}</option>`).join('');
}

async function createCharacter(event) {
    event.preventDefault();
    const name = document.getElementById('char-name').value;
    const class_id = document.getElementById('char-class').value;

    const res = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, class_id: parseInt(class_id) })
    });
    const data = await res.json();
    if (res.ok) {
        loadProfile();
    } else {
        alert(data.error);
    }
}

async function loadQuests() {
    const res = await fetch('/api/quests');
    const quests = await res.json();
    const container = document.getElementById('quests-container');
    
    container.innerHTML = quests.map(q => `
        <div class="col-md-4 mb-3">
            <div class="card bg-secondary text-light p-3 h-100">
                <h5>${q.title}</h5>
                <p>${q.description}</p>
                <p class="text-info mb-1">Recompensa: +${q.reward_xp} XP | +${q.reward_coins} 🪙</p>
                <p class="text-muted small">Nível Requerido: ${q.required_level}</p>
                <button class="btn ${q.completed ? 'btn-outline-success' : 'btn-primary'} mt-auto" 
                    ${q.completed ? 'disabled' : ''} onclick="completeQuest(${q.id})">
                    ${q.completed ? 'Concluída' : 'Completar Missão'}
                </button>
            </div>
        </div>
    `).join('');
}

async function completeQuest(questId) {
    const res = await fetch('/api/quests/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quest_id: questId })
    });
    const data = await res.json();
    if (res.ok) {
        alert(`Missão concluída! +${data.reward_xp} XP, +${data.reward_coins} Moedas.${data.leveled_up ? ' PARABÉNS! VOCÊ SUBIU DE NÍVEL!' : ''}`);
        loadQuests();
    } else {
        alert(data.error);
    }
}

async function loadShop() {
    const res = await fetch('/api/shop');
    const items = await res.json();
    const container = document.getElementById('shop-container');

    container.innerHTML = items.map(i => `
        <div class="col-md-4 mb-3">
            <div class="card bg-secondary text-light p-3 h-100">
                <h5>${i.name}</h5>
                <p>Tipo: ${i.item_type}</p>
                <p class="text-warning">Preço: 🪙 ${i.price}</p>
                <button class="btn btn-warning mt-auto" onclick="buyItem(${i.id})">Comprar</button>
            </div>
        </div>
    `).join('');
}

async function buyItem(itemId) {
    const res = await fetch('/api/shop/buy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId })
    });
    const data = await res.json();
    if (res.ok) {
        alert(data.message);
    } else {
        alert(data.error);
    }
}

async function loadInventory() {
    const res = await fetch('/api/inventory');
    const items = await res.json();
    const list = document.getElementById('inventory-list');
    list.innerHTML = items.length ? items.map(i => `<li class="list-group-item bg-transparent text-light border-secondary">⚔️ ${i.name} (${i.item_type})</li>`).join('') : '<li class="list-group-item bg-transparent text-muted border-secondary">Inventário vazio.</li>';
}

async function loadGuildAndBoss() {
    const bossRes = await fetch('/api/boss');
    const boss = await bossRes.json();
    const hpPercent = Math.max(0, (boss.current_hp / boss.max_hp) * 100);

    document.getElementById('boss-info').innerHTML = `
        <h5>${boss.name}</h5>
        <div class="progress mb-3 bg-dark" style="height: 25px;">
            <div class="progress-bar bg-danger" role="progressbar" style="width: ${hpPercent}%;">${boss.current_hp} / ${boss.max_hp} HP</div>
        </div>
        <p>${boss.is_defeated ? '🎉 O Chefe foi derrotado pela comunidade!' : '⚠️ O chefe continua atacando. Complete missões para causar dano!'}</p>
    `;

    const guildRes = await fetch('/api/guild');
    const members = await guildRes.json();
    document.getElementById('guild-list').innerHTML = members.map(m => `
        <li class="list-group-item bg-transparent text-light border-secondary d-flex justify-content-between align-items-center">
            ${m.name} (${m.class_name}) - Nv. ${m.level}
            <span class="badge bg-primary rounded-pill">@${m.username}</span>
        </li>
    `).join('');
}

async function logout() {
    await fetch('/api/logout', { method: 'POST' });
    location.reload();
}