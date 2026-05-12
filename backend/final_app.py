from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import json
from datetime import datetime, timedelta, date
from models import db, User, MenuItem, Order, OrderItem, OrderStatus, StaffRole, StaffActivity, Notification, Review
from sqlalchemy import func, desc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from io import BytesIO
import base64

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.secret_key = 'canteengo_final_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///canteengo_final.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default admin
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='staff', staff_role=StaffRole.ADMIN,
                        email='admin@canteengo.com', full_name='System Administrator')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        
        # Create sample customers
        if User.query.filter_by(role='student').count() == 0:
            sample_customers = [
                {'username': 'john_doe', 'email': 'john@student.edu', 'full_name': 'John Doe'},
                {'username': 'jane_smith', 'email': 'jane@student.edu', 'full_name': 'Jane Smith'},
                {'username': 'mike_wilson', 'email': 'mike@student.edu', 'full_name': 'Mike Wilson'},
                {'username': 'sarah_jones', 'email': 'sarah@student.edu', 'full_name': 'Sarah Jones'},
                {'username': 'alex_brown', 'email': 'alex@student.edu', 'full_name': 'Alex Brown'},
                {'username': 'emma_davis', 'email': 'emma@student.edu', 'full_name': 'Emma Davis'},
                {'username': 'ryan_taylor', 'email': 'ryan@student.edu', 'full_name': 'Ryan Taylor'},
                {'username': 'lisa_garcia', 'email': 'lisa@student.edu', 'full_name': 'Lisa Garcia'},
            ]
            
            for customer_data in sample_customers:
                customer = User(username=customer_data['username'], role='student', 
                              email=customer_data['email'], full_name=customer_data['full_name'])
                customer.set_password('password123')
                db.session.add(customer)
            db.session.commit()
        
        # Enhanced menu with premium food images
        if MenuItem.query.count() == 0:
            menu_items = [
                # Pizza Collection
                {'name': 'Margherita Pizza', 'price': 299, 'image': 'https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=500&h=400&fit=crop', 'description': 'Classic Italian pizza with fresh mozzarella, tomatoes, and basil leaves', 'category': 'Pizza', 'preparation_time': 20, 'calories': 250, 'ingredients': 'Mozzarella, Tomatoes, Basil, Pizza Dough'},
                {'name': 'Pepperoni Supreme', 'price': 399, 'image': 'https://images.unsplash.com/photo-1628840042765-356cda07504e?w=500&h=400&fit=crop', 'description': 'Loaded with premium pepperoni and extra cheese', 'category': 'Pizza', 'preparation_time': 22, 'calories': 320, 'ingredients': 'Pepperoni, Mozzarella, Pizza Sauce'},
                {'name': 'Veggie Deluxe', 'price': 349, 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=500&h=400&fit=crop', 'description': 'Garden fresh vegetables with herbs and cheese', 'category': 'Pizza', 'preparation_time': 25, 'calories': 280, 'ingredients': 'Bell Peppers, Mushrooms, Onions, Olives'},
                
                # Gourmet Burgers
                {'name': 'Classic Beef Burger', 'price': 249, 'image': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500&h=400&fit=crop', 'description': 'Juicy beef patty with lettuce, tomato, and special sauce', 'category': 'Burgers', 'preparation_time': 15, 'calories': 450, 'ingredients': 'Beef Patty, Lettuce, Tomato, Cheese'},
                {'name': 'Chicken Deluxe', 'price': 279, 'image': 'https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=500&h=400&fit=crop', 'description': 'Grilled chicken breast with avocado and bacon', 'category': 'Burgers', 'preparation_time': 18, 'calories': 420, 'ingredients': 'Chicken Breast, Avocado, Bacon, Mayo'},
                {'name': 'Veggie Burger', 'price': 199, 'image': 'https://images.unsplash.com/photo-1525059696034-4967a729002e?w=500&h=400&fit=crop', 'description': 'Plant-based patty with fresh vegetables', 'category': 'Burgers', 'preparation_time': 12, 'calories': 350, 'ingredients': 'Plant Patty, Lettuce, Tomato, Onion'},
                
                # Indian Specialties
                {'name': 'Butter Chicken', 'price': 399, 'image': 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=500&h=400&fit=crop', 'description': 'Creamy tomato curry with tender chicken pieces', 'category': 'Indian', 'preparation_time': 20, 'calories': 420, 'ingredients': 'Chicken, Tomato Sauce, Cream, Spices'},
                {'name': 'Chicken Biryani', 'price': 349, 'image': 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=500&h=400&fit=crop', 'description': 'Fragrant basmati rice with spiced chicken', 'category': 'Indian', 'preparation_time': 30, 'calories': 380, 'ingredients': 'Basmati Rice, Chicken, Saffron, Spices'},
                {'name': 'Paneer Tikka', 'price': 299, 'image': 'https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=500&h=400&fit=crop', 'description': 'Grilled cottage cheese with aromatic spices', 'category': 'Indian', 'preparation_time': 15, 'calories': 320, 'ingredients': 'Paneer, Yogurt, Spices, Bell Peppers'},
                
                # Pasta Paradise
                {'name': 'Spaghetti Carbonara', 'price': 279, 'image': 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=500&h=400&fit=crop', 'description': 'Creamy pasta with bacon and parmesan cheese', 'category': 'Pasta', 'preparation_time': 18, 'calories': 380, 'ingredients': 'Spaghetti, Bacon, Parmesan, Cream'},
                {'name': 'Penne Arrabbiata', 'price': 249, 'image': 'https://images.unsplash.com/photo-1572441713132-51c75654db73?w=500&h=400&fit=crop', 'description': 'Spicy tomato sauce with penne pasta', 'category': 'Pasta', 'preparation_time': 16, 'calories': 340, 'ingredients': 'Penne, Tomatoes, Chili, Garlic'},
                
                # Fresh Salads
                {'name': 'Caesar Salad', 'price': 179, 'image': 'https://images.unsplash.com/photo-1546793665-c74683f339c1?w=500&h=400&fit=crop', 'description': 'Fresh romaine lettuce with Caesar dressing', 'category': 'Salads', 'preparation_time': 10, 'calories': 180, 'ingredients': 'Romaine, Caesar Dressing, Croutons'},
                {'name': 'Greek Salad', 'price': 199, 'image': 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500&h=400&fit=crop', 'description': 'Mediterranean salad with feta and olives', 'category': 'Salads', 'preparation_time': 8, 'calories': 200, 'ingredients': 'Feta, Olives, Cucumber, Tomatoes'},
                
                # Snacks & Appetizers
                {'name': 'Loaded Nachos', 'price': 199, 'image': 'https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?w=500&h=400&fit=crop', 'description': 'Crispy nachos with cheese and jalapeños', 'category': 'Snacks', 'preparation_time': 12, 'calories': 380, 'ingredients': 'Tortilla Chips, Cheese, Jalapeños'},
                {'name': 'Buffalo Wings', 'price': 249, 'image': 'https://images.unsplash.com/photo-1608039755401-742074f0548d?w=500&h=400&fit=crop', 'description': 'Spicy buffalo chicken wings', 'category': 'Snacks', 'preparation_time': 18, 'calories': 280, 'ingredients': 'Chicken Wings, Buffalo Sauce'},
                
                # Beverages
                {'name': 'Chocolate Milkshake', 'price': 149, 'image': 'https://images.unsplash.com/photo-1579954115545-a95591f28bfc?w=500&h=400&fit=crop', 'description': 'Rich chocolate milkshake with whipped cream', 'category': 'Drinks', 'preparation_time': 5, 'calories': 280, 'ingredients': 'Milk, Chocolate, Ice Cream'},
                {'name': 'Fresh Orange Juice', 'price': 89, 'image': 'https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?w=500&h=400&fit=crop', 'description': 'Freshly squeezed orange juice', 'category': 'Drinks', 'preparation_time': 3, 'calories': 120, 'ingredients': 'Fresh Oranges'},
                {'name': 'Iced Coffee', 'price': 129, 'image': 'https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500&h=400&fit=crop', 'description': 'Cold brew coffee with ice and cream', 'category': 'Drinks', 'preparation_time': 4, 'calories': 50, 'ingredients': 'Coffee, Ice, Cream'},
                
                # Desserts
                {'name': 'Chocolate Lava Cake', 'price': 199, 'image': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500&h=400&fit=crop', 'description': 'Warm chocolate cake with molten center', 'category': 'Desserts', 'preparation_time': 8, 'calories': 380, 'ingredients': 'Chocolate, Butter, Eggs, Flour'},
                {'name': 'Ice Cream Sundae', 'price': 149, 'image': 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500&h=400&fit=crop', 'description': 'Vanilla ice cream with chocolate sauce', 'category': 'Desserts', 'preparation_time': 3, 'calories': 250, 'ingredients': 'Ice Cream, Chocolate Sauce, Nuts'},
            ]
            
            for item in menu_items:
                db.session.add(MenuItem(**item))
            db.session.commit()
        
        # Create sample orders
        if Order.query.count() == 0:
            import random
            from datetime import timedelta
            
            customers = User.query.filter_by(role='student').all()
            menu_items = MenuItem.query.all()
            
            if customers and menu_items:
                # Create orders for the last 7 days
                for days_ago in range(7):
                    order_date = datetime.now() - timedelta(days=days_ago)
                    
                    # Create 3-8 orders per day
                    num_orders = random.randint(3, 8)
                    
                    for _ in range(num_orders):
                        customer = random.choice(customers)
                        
                        # Random order time during business hours (9 AM - 9 PM)
                        hour = random.randint(9, 21)
                        minute = random.randint(0, 59)
                        order_time = order_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # Create order
                        order = Order(
                            user_id=customer.id,
                            timestamp=order_time,
                            payment_method=random.choice(['cash', 'card', 'upi', 'wallet']),
                            special_instructions=random.choice([
                                '', 'Extra spicy', 'No onions', 'Less salt', 'Extra cheese',
                                'Make it crispy', 'Well done', 'Medium spice'
                            ])
                        )
                        
                        # Set random status (more recent orders are more likely to be pending/preparing)
                        if days_ago == 0:  # Today's orders
                            status_choices = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY]
                            order.status = random.choice(status_choices)
                        elif days_ago <= 2:  # Recent orders
                            status_choices = [OrderStatus.READY, OrderStatus.COMPLETED, OrderStatus.COMPLETED, OrderStatus.COMPLETED]
                            order.status = random.choice(status_choices)
                        else:  # Older orders
                            order.status = OrderStatus.COMPLETED
                        
                        db.session.add(order)
                        db.session.flush()  # Get the order ID
                        
                        # Add 1-4 items to each order
                        num_items = random.randint(1, 4)
                        selected_items = random.sample(menu_items, min(num_items, len(menu_items)))
                        
                        total = 0
                        for menu_item in selected_items:
                            quantity = random.randint(1, 3)
                            order_item = OrderItem(
                                order_id=order.id,
                                menu_item_id=menu_item.id,
                                quantity=quantity,
                                price=menu_item.price
                            )
                            total += menu_item.price * quantity
                            db.session.add(order_item)
                        
                        order.total = total
                        order.estimated_time = random.randint(15, 45)
                
                db.session.commit()
                print(f"Created {Order.query.count()} sample orders")

# Analytics Functions
def generate_analytics():
    """Generate analytics charts"""
    try:
        orders = Order.query.all()
        if not orders:
            return None
        
        # Create data
        order_data = []
        for order in orders:
            for item in order.items:
                order_data.append({
                    'date': order.timestamp.date(),
                    'hour': order.timestamp.hour,
                    'item_name': item.menu_item.name,
                    'category': item.menu_item.category,
                    'quantity': item.quantity,
                    'revenue': item.price * item.quantity
                })
        
        if not order_data:
            return None
        
        df = pd.DataFrame(order_data)
        
        # Set style
        plt.style.use('default')
        
        charts = {}
        
        # Chart 1: Category Revenue
        fig, ax = plt.subplots(figsize=(10, 6))
        category_revenue = df.groupby('category')['revenue'].sum().sort_values(ascending=False)
        bars = ax.bar(category_revenue.index, category_revenue.values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
        ax.set_title('Revenue by Category', fontsize=16, fontweight='bold')
        ax.set_ylabel('Revenue (₹)')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 10,
                   f'₹{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        img = BytesIO()
        plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
        img.seek(0)
        charts['category'] = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        # Chart 2: Popular Items
        fig, ax = plt.subplots(figsize=(12, 6))
        popular_items = df.groupby('item_name')['quantity'].sum().sort_values(ascending=False).head(8)
        bars = ax.bar(range(len(popular_items)), popular_items.values, color='#667eea')
        ax.set_title('Most Popular Items', fontsize=16, fontweight='bold')
        ax.set_ylabel('Quantity Sold')
        ax.set_xticks(range(len(popular_items)))
        ax.set_xticklabels(popular_items.index, rotation=45, ha='right')
        
        # Add value labels
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        img = BytesIO()
        plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
        img.seek(0)
        charts['popular'] = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return charts
    except Exception as e:
        print(f"Analytics error: {e}")
        return None

# Routes
@app.route('/')
def landing_page():
    return render_template('super_landing.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='student').first()
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            session['user_id'] = user.id
            session['user'] = 'student'
            session['username'] = username
            return redirect(url_for('student_menu'))
        else:
            return render_template('student_login_super.html', error='Invalid credentials')
    return render_template('student_login_super.html')

@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        full_name = request.form.get('full_name', '')

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return render_template('student_register_super.html', error='Username already exists')
        
        # Check if email already exists (if email is provided)
        if email and User.query.filter_by(email=email).first():
            return render_template('student_register_super.html', error='Email already exists. Please use a different email or login.')

        user = User(username=username, role='student', email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return render_template('student_register_super.html', success='Account created! Please login to continue.')
    return render_template('student_register_super.html')

@app.route('/student_menu')
def student_menu():
    # Remove login requirement for testing
    # if 'user' not in session or session['user'] != 'student':
    #     return redirect(url_for('student_login'))
    
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    
    # Get recommendations based on user's order history
    user_orders = Order.query.filter_by(user_id=session['user_id']).all()
    recommended_items = []
    
    if user_orders:
        ordered_categories = []
        for order in user_orders:
            for item in order.items:
                ordered_categories.append(item.menu_item.category)
        
        if ordered_categories:
            most_common_category = max(set(ordered_categories), key=ordered_categories.count)
            recommended_items = MenuItem.query.filter_by(
                category=most_common_category, 
                is_available=True
            ).limit(3).all()
    
    return render_template('student_menu_super.html', 
                         menu=menu_items, 
                         recommendations=recommended_items)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        # Get data from either JSON or form
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'})
            
        item_id = int(data.get('item_id', 0))
        quantity = int(data.get('quantity', 1))
        
        if not item_id:
            return jsonify({'success': False, 'message': 'Item ID is required'})
        
        # Initialize cart if not exists
        if 'cart' not in session:
            session['cart'] = []
        
        menu_item = MenuItem.query.get(item_id)
        
        if menu_item:
            # Check if item already exists in cart
            found = False
            for item in session['cart']:
                if int(item['id']) == item_id:
                    item['quantity'] += quantity
                    found = True
                    break
            
            if not found:
                cart_item = {
                    'id': item_id,
                    'name': menu_item.name,
                    'price': float(menu_item.price),
                    'quantity': quantity,
                    'image': menu_item.image or ''
                }
                session['cart'].append(cart_item)
            
            session.modified = True
            return jsonify({
                'success': True, 
                'cart_count': len(session['cart']), 
                'message': f'{menu_item.name} added to cart!'
            })
        
        return jsonify({'success': False, 'message': 'Item not found'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/view_cart')
def view_cart():
    cart = session.get('cart', [])
    total = sum(float(item['price']) * int(item['quantity']) for item in cart)
    
    return render_template('cart_super.html', cart=cart, total=total)

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user' not in session or session['user'] != 'student':
        return redirect(url_for('student_login'))
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        cart = session.get('cart', [])
        special_instructions = request.form.get('special_instructions', '')
        
        if not cart:
            flash('Your cart is empty!', 'error')
            return redirect(url_for('student_menu'))
        
        # Create order
        total = sum(item['price'] * item['quantity'] for item in cart)
        order = Order(
            user_id=session['user_id'], 
            total=total, 
            payment_method=payment_method,
            special_instructions=special_instructions
        )
        db.session.add(order)
        db.session.commit()
        
        # Add order items
        for item in cart:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item['id'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)
        
        order.calculate_estimated_time()
        db.session.commit()
        
        # Clear cart
        session.pop('cart', None)
        
        return render_template('payment_success_super.html', order=order)
    
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('payment_super.html', cart=cart, total=total)

@app.route('/staff_login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='staff', is_active=True).first()

        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            session['user_id'] = user.id
            session['user'] = 'staff'
            session['staff_role'] = user.staff_role.value if user.staff_role else 'staff'
            session['username'] = username
            return redirect(url_for('staff_dashboard'))
        else:
            return render_template('staff_login_super.html', error='Invalid credentials')
    return render_template('staff_login_super.html')

@app.route('/staff_dashboard')
def staff_dashboard():
    if 'user' not in session or session['user'] != 'staff':
        return redirect(url_for('staff_login'))

    user = User.query.get(session['user_id'])
    
    # Get orders by status
    pending_orders = Order.query.filter_by(status=OrderStatus.PENDING).order_by(desc(Order.timestamp)).all()
    preparing_orders = Order.query.filter_by(status=OrderStatus.PREPARING).all()
    ready_orders = Order.query.filter_by(status=OrderStatus.READY).all()

    # Today's stats
    today = datetime.now().date()
    today_orders = Order.query.filter(func.date(Order.timestamp) == today).all()
    today_sales = sum(order.total for order in today_orders)
    
    # Generate analytics charts
    charts = generate_analytics()
    
    # Get popular items
    popular_items = db.session.query(
        MenuItem.name,
        func.sum(OrderItem.quantity).label('total_sold')
    ).join(OrderItem).group_by(MenuItem.id).order_by(desc('total_sold')).limit(5).all()

    return render_template('staff_dashboard_super.html',
                         user=user,
                         pending_orders=pending_orders,
                         preparing_orders=preparing_orders,
                         ready_orders=ready_orders,
                         today_sales=today_sales,
                         today_orders=len(today_orders),
                         charts=charts,
                         popular_items=popular_items)

@app.route('/update_order_status/<int:order_id>/<status>')
def update_order_status(order_id, status):
    if 'user' not in session or session['user'] != 'staff':
        return redirect(url_for('staff_login'))

    order = Order.query.get_or_404(order_id)
    
    try:
        new_status = OrderStatus(status)
        order.update_status(new_status)
        flash(f'Order #{order_id} updated to {status}', 'success')
    except ValueError:
        flash('Invalid status', 'error')

    return redirect(url_for('staff_dashboard'))

@app.route('/student_orders')
def student_orders():
    if 'user' not in session or session['user'] != 'student':
        return redirect(url_for('student_login'))
    
    user_id = session['user_id']
    orders = Order.query.filter_by(user_id=user_id).order_by(desc(Order.timestamp)).all()
    
    return render_template('student_orders_super.html', orders=orders)

# Enhanced Staff Routes
@app.route('/staff/menu_management')
def menu_management():
    if 'user' not in session or session['user'] != 'staff':
        return redirect(url_for('staff_login'))
    
    menu_items = MenuItem.query.all()
    categories = db.session.query(MenuItem.category).distinct().all()
    
    return render_template('staff_menu_management.html', 
                         menu_items=menu_items, 
                         categories=[c[0] for c in categories])

@app.route('/staff/add_menu_item', methods=['POST'])
def add_menu_item():
    if 'user' not in session or session['user'] != 'staff':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    
    new_item = MenuItem(
        name=data['name'],
        price=float(data['price']),
        description=data['description'],
        category=data['category'],
        image=data.get('image', ''),
        preparation_time=int(data.get('preparation_time', 15)),
        calories=int(data.get('calories', 0)),
        ingredients=data.get('ingredients', ''),
        is_available=True
    )
    
    db.session.add(new_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Menu item added successfully'})

@app.route('/staff/toggle_item/<int:item_id>')
def toggle_item_availability(item_id):
    if 'user' not in session or session['user'] != 'staff':
        return jsonify({'success': False})
    
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    db.session.commit()
    
    return jsonify({'success': True, 'available': item.is_available})

@app.route('/staff/analytics')
def staff_analytics():
    if 'user' not in session or session['user'] != 'staff':
        return redirect(url_for('staff_login'))
    
    # Advanced analytics data
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Sales data
    today_sales = db.session.query(func.sum(Order.total)).filter(
        func.date(Order.timestamp) == today
    ).scalar() or 0
    
    # Order counts
    today_orders = Order.query.filter(func.date(Order.timestamp) == today).count()
    pending_orders = Order.query.filter_by(status=OrderStatus.PENDING).count()
    
    # Popular items
    popular_items = db.session.query(
        MenuItem.name,
        MenuItem.category,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.price * OrderItem.quantity).label('revenue')
    ).join(OrderItem).join(Order).filter(
        func.date(Order.timestamp) >= week_ago
    ).group_by(MenuItem.id).order_by(desc('total_sold')).limit(10).all()
    
    # Category performance
    category_stats = db.session.query(
        MenuItem.category,
        func.sum(OrderItem.quantity).label('items_sold'),
        func.sum(OrderItem.price * OrderItem.quantity).label('revenue')
    ).join(OrderItem).join(Order).filter(
        func.date(Order.timestamp) >= week_ago
    ).group_by(MenuItem.category).all()
    
    # Hourly sales pattern
    hourly_sales = db.session.query(
        func.strftime('%H', Order.timestamp).label('hour'),
        func.count(Order.id).label('order_count')
    ).filter(
        func.date(Order.timestamp) >= week_ago
    ).group_by('hour').all()
    
    return render_template('staff_analytics.html',
                         today_sales=today_sales,
                         today_orders=today_orders,
                         pending_orders=pending_orders,
                         popular_items=popular_items,
                         category_stats=category_stats,
                         hourly_sales=hourly_sales)

@app.route('/staff/inventory')
def inventory_management():
    if 'user' not in session or session['user'] != 'staff':
        return redirect(url_for('staff_login'))
    
    menu_items = MenuItem.query.all()
    return render_template('staff_inventory.html', menu_items=menu_items)

@app.route('/staff/orders_advanced')
def advanced_order_management():
    if 'user' not in session or session['user'] != 'staff':
        return redirect(url_for('staff_login'))
    
    orders = Order.query.order_by(desc(Order.timestamp)).limit(50).all()
    return render_template('staff_orders_advanced.html', orders=orders)

@app.route('/staff/customer_management')
def customer_management():
    if 'user' not in session or session['user'] != 'staff':
        return redirect(url_for('staff_login'))
    
    customer_rows = db.session.query(
        User,
        func.count(Order.id).label('total_orders'),
        func.sum(Order.total).label('total_spent')
    ).outerjoin(Order, User.id == Order.user_id).filter(User.role == 'student').group_by(User.id).all()

    customers = [
        (row[0], row[1] or 0, row[2] or 0)
        for row in customer_rows
    ]
    total_revenue = sum(row[2] for row in customers)
    vip_count = sum(1 for row in customers if row[2] >= 2000)
    total_orders = sum(row[1] for row in customers)
    avg_lifetime_value = round(total_revenue / (total_orders or 1))

    return render_template(
        'staff_customers.html',
        customers=customers,
        total_revenue=total_revenue,
        vip_count=vip_count,
        avg_lifetime_value=avg_lifetime_value
    )

@app.route('/staff/seed_data')
def seed_sample_data():
    if 'user' not in session or session['user'] != 'staff':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    import random
    
    # Create sample customers if they don't exist
    sample_customers = [
        {'username': 'john_doe', 'email': 'john@student.edu', 'full_name': 'John Doe'},
        {'username': 'jane_smith', 'email': 'jane@student.edu', 'full_name': 'Jane Smith'},
        {'username': 'mike_wilson', 'email': 'mike@student.edu', 'full_name': 'Mike Wilson'},
        {'username': 'sarah_jones', 'email': 'sarah@student.edu', 'full_name': 'Sarah Jones'},
        {'username': 'alex_brown', 'email': 'alex@student.edu', 'full_name': 'Alex Brown'},
        {'username': 'emma_davis', 'email': 'emma@student.edu', 'full_name': 'Emma Davis'},
        {'username': 'ryan_taylor', 'email': 'ryan@student.edu', 'full_name': 'Ryan Taylor'},
        {'username': 'lisa_garcia', 'email': 'lisa@student.edu', 'full_name': 'Lisa Garcia'},
    ]
    
    customers_created = 0
    for customer_data in sample_customers:
        if not User.query.filter_by(username=customer_data['username']).first():
            customer = User(
                username=customer_data['username'], 
                role='student', 
                email=customer_data['email'], 
                full_name=customer_data['full_name']
            )
            customer.set_password('password123')
            db.session.add(customer)
            customers_created += 1
    
    db.session.commit()
    
    # Get all customers and menu items
    customers = User.query.filter_by(role='student').all()
    menu_items = MenuItem.query.all()
    
    if not customers or not menu_items:
        return jsonify({'success': False, 'message': 'No customers or menu items found'})
    
    # Create sample orders for the last 3 days
    orders_created = 0
    for days_ago in range(3):
        order_date = datetime.now() - timedelta(days=days_ago)
        
        # Create 8-15 orders per day
        num_orders = random.randint(8, 15)
        
        for _ in range(num_orders):
            customer = random.choice(customers)
            
            # Random order time during business hours (8 AM - 10 PM)
            hour = random.randint(8, 22)
            minute = random.randint(0, 59)
            order_time = order_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Create order
            order = Order(
                user_id=customer.id,
                timestamp=order_time,
                total=0.0,  # Temporary, will be updated after adding items
                payment_method=random.choice(['Cash', 'Card', 'UPI', 'Wallet']),
                special_instructions=random.choice([
                    '', 'Extra spicy please', 'No onions', 'Less salt', 'Extra cheese',
                    'Make it crispy', 'Well done', 'Medium spice', 'Extra sauce'
                ])
            )
            
            # Set realistic status based on order age
            if days_ago == 0:  # Today's orders
                if hour >= datetime.now().hour - 1:
                    order.status = random.choice([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING])
                else:
                    order.status = random.choice([OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.COMPLETED])
            else:  # Older orders
                order.status = OrderStatus.COMPLETED
            
            db.session.add(order)
            db.session.flush()  # Get the order ID
            
            # Add 1-4 items to each order
            num_items = random.randint(1, 4)
            selected_items = random.sample(menu_items, min(num_items, len(menu_items)))
            
            total = 0
            for menu_item in selected_items:
                quantity = random.randint(1, 3)
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    quantity=quantity,
                    price=menu_item.price
                )
                total += menu_item.price * quantity
                db.session.add(order_item)
            
            order.total = total
            order.estimated_time = random.randint(10, 45)
            orders_created += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Created {customers_created} customers and {orders_created} orders',
        'customers_created': customers_created,
        'orders_created': orders_created
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing_page'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5007)