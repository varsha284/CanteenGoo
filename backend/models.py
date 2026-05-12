from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

class OrderStatus(Enum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    PREPARING = 'preparing'
    READY = 'ready'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class StaffRole(Enum):
    ADMIN = 'admin'
    MANAGER = 'manager'
    CHEF = 'chef'
    CASHIER = 'cashier'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'staff'
    staff_role = db.Column(db.Enum(StaffRole), nullable=True)  # Only for staff
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, default=100)
    preparation_time = db.Column(db.Integer, default=15)  # in minutes
    calories = db.Column(db.Integer, nullable=True)
    ingredients = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_method = db.Column(db.String(50), default='cash')
    special_instructions = db.Column(db.Text, nullable=True)
    estimated_time = db.Column(db.Integer, nullable=True)  # in minutes
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('orders', lazy=True))
    assigned_staff = db.relationship('User', foreign_keys=[assigned_staff_id])
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def update_status(self, new_status):
        self.status = new_status
        if new_status == OrderStatus.COMPLETED:
            self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def calculate_estimated_time(self):
        total_time = sum(item.menu_item.preparation_time * item.quantity for item in self.items)
        self.estimated_time = max(total_time, 10)  # minimum 10 minutes
        db.session.commit()

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    special_requests = db.Column(db.Text, nullable=True)
    menu_item = db.relationship('MenuItem', backref=db.backref('order_items', lazy=True))

class StaffActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    staff = db.relationship('User', backref=db.backref('activities', lazy=True))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    order = db.relationship('Order', backref=db.backref('review', uselist=False, lazy=True))
