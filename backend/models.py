from datetime import datetime
from backend.database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    character = db.relationship('Character', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class GameClass(db.Model):
    __tablename__ = 'game_classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    base_hp = db.Column(db.Integer, default=100)
    base_atk = db.Column(db.Integer, default=10)


class Character(db.Model):
    __tablename__ = 'characters'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('game_classes.id'), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    coins = db.Column(db.Integer, default=50)
    
    game_class = db.relationship('GameClass', backref='characters')
    inventory = db.relationship('Inventory', backref='character', cascade='all, delete-orphan')
    quest_logs = db.relationship('QuestLog', backref='character', cascade='all, delete-orphan')


class Quest(db.Model):
    __tablename__ = 'quests'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    reward_xp = db.Column(db.Integer, default=50)
    reward_coins = db.Column(db.Integer, default=20)
    required_level = db.Column(db.Integer, default=1)


class QuestLog(db.Model):
    __tablename__ = 'quest_logs'
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quests.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    quest = db.relationship('Quest', backref='logs')


class ShopItem(db.Model):
    __tablename__ = 'shop_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # weapon, armor, potion
    price = db.Column(db.Integer, nullable=False)
    stat_bonus = db.Column(db.Integer, default=0)


class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_items.id'), nullable=False)
    
    item = db.relationship('ShopItem', backref='inventories')


class CommunityBoss(db.Model):
    __tablename__ = 'community_boss'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    max_hp = db.Column(db.Integer, default=1000)
    current_hp = db.Column(db.Integer, default=1000)
    is_defeated = db.Column(db.Boolean, default=False)