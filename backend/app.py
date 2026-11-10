
import os

from flask import Flask, send_from_directory

from backend.database import db
from backend.routes import api
from backend.models import GameClass, Quest, ShopItem, CommunityBoss


# Caminho absoluto da pasta frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))


def create_app():
    app = Flask(
        __name__,
        static_folder=FRONTEND_DIR,
        static_url_path=''
    )

    app.config['SECRET_KEY'] = 'lifequest-secret-key-acad'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lifequest.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(api)

    @app.route('/')
    def index():
        return send_from_directory(FRONTEND_DIR, 'index.html')

    with app.app_context():
        db.create_all()
        seed_database()

    return app


def seed_database():
    if not GameClass.query.first():
        classes = [
            GameClass(
                name='Guerreiro',
                description='Especialista em combate corpo a corpo e alta resistência.',
                base_hp=120,
                base_atk=15
            ),
            GameClass(
                name='Mago',
                description='Mestre nas artes arcanas com alto poder de dano mágico.',
                base_hp=80,
                base_atk=25
            ),
            GameClass(
                name='Ladino',
                description='Ágil e furtivo, especializado em ataques rápidos.',
                base_hp=90,
                base_atk=20
            )
        ]

        db.session.bulk_save_objects(classes)
        db.session.commit()

    if not Quest.query.first():
        quests = [
            Quest(
                title='Primeiros Passos',
                description='Complete seu cadastro e explore o painel.',
                reward_xp=40,
                reward_coins=15,
                required_level=1
            ),
            Quest(
                title='Caça aos Goblins',
                description='Derrote os monstros na floresta de Parelhas.',
                reward_xp=80,
                reward_coins=30,
                required_level=1
            ),
            Quest(
                title='O Desafio do Arcano',
                description='Estude os pergaminhos antigos da biblioteca.',
                reward_xp=150,
                reward_coins=60,
                required_level=2
            )
        ]

        db.session.bulk_save_objects(quests)
        db.session.commit()

    if not ShopItem.query.first():
        items = [
            ShopItem(name='Espada de Ferro', item_type='weapon', price=50, stat_bonus=10),
            ShopItem(name='Armadura de Couro', item_type='armor', price=40, stat_bonus=15),
            ShopItem(name='Poção de Cura', item_type='potion', price=20, stat_bonus=50)
        ]

        db.session.bulk_save_objects(items)
        db.session.commit()

    if not CommunityBoss.query.first():
        boss = CommunityBoss(
            name='Dragão Ancestral do Seridó',
            max_hp=1000,
            current_hp=1000,
            is_defeated=False
        )

        db.session.add(boss)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
