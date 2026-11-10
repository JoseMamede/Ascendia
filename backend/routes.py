from flask import Blueprint, request, jsonify, session
from backend.database import db
from backend.models import User, GameClass, Character, Quest, QuestLog, ShopItem, Inventory, CommunityBoss

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'Preencha todos os campos obrigatórios.'}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'Nome de usuário ou e-mail já cadastrados.'}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Usuário cadastrado com sucesso!'}), 201


@api.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Credenciais inválidas.'}), 401

    session['user_id'] = user.id
    return jsonify({'message': 'Login realizado com sucesso!', 'username': user.username})


@api.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout realizado com sucesso!'})


@api.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Não autorizado.'}), 401

    user = User.query.get(user_id)

    if request.method == 'GET':
        char = user.character
        char_data = None
        if char:
            char_data = {
                'id': char.id,
                'name': char.name,
                'class_name': char.game_class.name,
                'level': char.level,
                'experience': char.experience,
                'next_level_xp': char.level * 100,
                'coins': char.coins
            }
        return jsonify({
            'username': user.username,
            'email': user.email,
            'character': char_data
        })

    # POST: Criar personagem se não existir
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    class_id = data.get('class_id')

    if user.character:
        return jsonify({'error': 'Personagem já criado para este usuário.'}), 400

    if not name or not class_id:
        return jsonify({'error': 'Nome e classe são obrigatórios.'}), 400

    game_class = GameClass.query.get(class_id)
    if not game_class:
        return jsonify({'error': 'Classe inválida.'}), 400

    character = Character(user_id=user.id, name=name, class_id=game_class.id)
    db.session.add(character)
    db.session.commit()

    return jsonify({'message': 'Personagem criado com sucesso!'}), 201


@api.route('/classes', methods=['GET'])
def get_classes():
    classes = GameClass.query.all()
    return jsonify([{'id': c.id, 'name': c.name, 'description': c.description} for c in classes])


@api.route('/quests', methods=['GET'])
def get_quests():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Não autorizado.'}), 401

    user = User.query.get(user_id)
    if not user.character:
        return jsonify({'error': 'Crie um personagem primeiro.'}), 400

    quests = Quest.query.all()
    completed_quest_ids = {log.quest_id for log in user.character.quest_logs}

    result = []
    for q in quests:
        result.append({
            'id': q.id,
            'title': q.title,
            'description': q.description,
            'reward_xp': q.reward_xp,
            'reward_coins': q.reward_coins,
            'required_level': q.required_level,
            'completed': q.id in completed_quest_ids
        })
    return jsonify(result)


@api.route('/quests/complete', methods=['POST'])
def complete_quest():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Não autorizado.'}), 401

    data = request.get_json() or {}
    quest_id = data.get('quest_id')

    user = User.query.get(user_id)
    char = user.character
    if not char:
        return jsonify({'error': 'Personagem não encontrado.'}), 400

    # 1. Verificar se a missão existe
    quest = Quest.query.get(quest_id)
    if not quest:
        return jsonify({'error': 'Missão não encontrada.'}), 404

    # 2. Verificar se o jogador pode concluí-la (Nível mínimo e se já não foi concluída)
    if char.level < quest.required_level:
        return jsonify({'error': 'Nível insuficiente para esta missão.'}), 400

    already_completed = QuestLog.query.filter_by(character_id=char.id, quest_id=quest.id).first()
    if already_completed:
        return jsonify({'error': 'Missão já concluída anteriormente.'}), 400

    # 3. Registrar sua conclusão
    log = QuestLog(character_id=char.id, quest_id=quest.id)
    db.session.add(log)

    # 4. Calcular e adicionar o XP & 5. Adicionar as moedas
    char.experience += quest.reward_xp
    char.coins += quest.reward_coins

    # 6. Verificar se o personagem subiu de nível (Regra: XP necessário = Nível * 100)
    leveled_up = False
    xp_needed = char.level * 100
    while char.experience >= xp_needed:
        char.experience -= xp_needed
        char.level += 1
        leveled_up = True
        xp_needed = char.level * 100

    # 7. Atualizar o progresso do chefe comunitário (Causar dano baseado no XP da missão)
    boss = CommunityBoss.query.first()
    if boss and not boss.is_defeated:
        boss.current_hp -= quest.reward_xp
        if boss.current_hp <= 0:
            boss.current_hp = 0
            boss.is_defeated = True

    db.session.commit()

    return jsonify({
        'message': 'Missão concluída com sucesso!',
        'reward_xp': quest.reward_xp,
        'reward_coins': quest.reward_coins,
        'leveled_up': leveled_up,
        'new_level': char.level,
        'new_xp': char.experience,
        'new_coins': char.coins,
        'boss_hp': boss.current_hp if boss else 0
    })


@api.route('/shop', methods=['GET'])
def get_shop():
    items = ShopItem.query.all()
    return jsonify([{'id': i.id, 'name': i.name, 'item_type': i.item_type, 'price': i.price, 'stat_bonus': i.stat_bonus} for i in items])


@api.route('/shop/buy', methods=['POST'])
def buy_item():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Não autorizado.'}), 401

    data = request.get_json() or {}
    item_id = data.get('item_id')

    user = User.query.get(user_id)
    char = user.character
    if not char:
        return jsonify({'error': 'Personagem não encontrado.'}), 400

    item = ShopItem.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item não encontrado.'}), 404

    if char.coins < item.price:
        return jsonify({'error': 'Moedas insuficientes.'}), 400

    char.coins -= item.price
    inv_item = Inventory(character_id=char.id, item_id=item.id)
    db.session.add(inv_item)
    db.session.commit()

    return jsonify({'message': f'Item {item.name} adquirido com sucesso!', 'remaining_coins': char.coins})


@api.route('/inventory', methods=['GET'])
def get_inventory():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Não autorizado.'}), 401

    user = User.query.get(user_id)
    char = user.character
    if not char:
        return jsonify({'error': 'Personagem não encontrado.'}), 400

    items = []
    for inv in char.inventory:
        items.append({
            'id': inv.item.id,
            'name': inv.item.name,
            'item_type': inv.item.item_type,
            'stat_bonus': inv.item.stat_bonus
        })
    return jsonify(items)


@api.route('/boss', methods=['GET'])
def get_boss():
    boss = CommunityBoss.query.first()
    if not boss:
        return jsonify({'name': 'Nenhum chefe ativo', 'max_hp': 1000, 'current_hp': 1000, 'is_defeated': False})
    return jsonify({
        'name': boss.name,
        'max_hp': boss.max_hp,
        'current_hp': boss.current_hp,
        'is_defeated': boss.is_defeated
    })


@api.route('/guild', methods=['GET'])
def get_guild():
    # Retorna uma lista simulada de membros da guilda (outros personagens cadastrados)
    characters = Character.query.all()
    guild_members = []
    for c in characters:
        guild_members.append({
            'name': c.name,
            'class_name': c.game_class.name,
            'level': c.level,
            'username': c.user.username
        })
    return jsonify(guild_members)