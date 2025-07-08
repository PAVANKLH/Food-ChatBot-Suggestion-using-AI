import logging
import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import secrets
import string

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///orders.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    from db_models import User
    return User.query.get(int(user_id))

# Food menu data with images
MENU_ITEMS = [
    # Hyderabadi Biryanis
    {"id": 1, "name": "Hyderabadi Chicken Biryani", "description": "Authentic Hyderabadi dum biryani with tender chicken and aromatic basmati rice", "price": 18.99, "category": "Biryani", "image": "https://th.bing.com/th/id/OIP.LMrVUyc4CLKdSwVXPrW3ywHaE8?w=274&h=183&c=7&r=0&o=7&pid=1.7&rm=3"},
    {"id": 2, "name": "Mutton Biryani", "description": "Premium mutton pieces cooked with fragrant spices and saffron rice", "price": 22.99, "category": "Biryani", "image": "https://kitchenofdebjani.com/wp-content/uploads/2018/10/Royal-Indian-Hotel-Mutton-Biryani.jpg"},
    {"id": 3, "name": "Hyderabadi Vegetable Biryani", "description": "Mixed vegetables layered with aromatic basmati rice and dum cooked", "price": 15.99, "category": "Biryani", "image": "https://th.bing.com/th/id/OIP.mqsjhI7s7syKm5lN5IPGdAHaEK?w=272&h=180&c=7&r=0&o=7&pid=1.7&rm=3"},
    {"id": 4, "name": "Fish Biryani", "description": "Fresh fish marinated in spices and cooked with fragrant rice", "price": 19.99, "category": "Biryani", "image": "https://as2.ftcdn.net/v2/jpg/04/18/22/51/1000_F_418225117_RHkXwPGZ20Ajrzzad59nGIidLY9vhj6y.jpg"},
    {"id": 5, "name": "Prawn Biryani", "description": "Succulent prawns with aromatic spices and basmati rice", "price": 21.99, "category": "Biryani", "image": "https://i.ytimg.com/vi/yUntK4Vdqfw/maxresdefault.jpg"},

    # Hyderabadi Non-Veg Specials
    {"id": 6, "name": "Mutton Marag", "description": "Traditional Hyderabadi mutton curry with rich, flavorful gravy", "price": 20.99, "category": "Non-Veg", "image": "https://wirally.com/wp-content/uploads/2023/03/Best-Mutton-Marag-In-Hyderabad1-696x392.jpg"},
    {"id": 7, "name": "Chicken Haleem", "description": "Slow-cooked lentils with tender chicken, a Hyderabadi favorite", "price": 16.99, "category": "Non-Veg", "image": "https://www.thedeliciouscrescent.com/wp-content/uploads/2020/08/Haleem-4.jpg"},
    {"id": 8, "name": "Hyderabadi Chicken Korma", "description": "Creamy chicken curry with cashews and aromatic spices", "price": 17.99, "category": "Non-Veg", "image": "https://th.bing.com/th/id/OIP.EsGHsvXoydIiinWXHvkJ5AHaE8?w=301&h=200&c=7&r=0&o=7&pid=1.7&rm=3"},
    {"id": 9, "name": "Keema Kaleji", "description": "Spiced minced mutton with liver, cooked Hyderabadi style", "price": 18.99, "category": "Non-Veg", "image": "https://i.pinimg.com/736x/48/3a/ea/483aeafedff00d056ecbb32b29c55d33.jpg"},
    {"id": 10, "name": "Chicken Tikka Masala", "description": "Tandoor grilled chicken in rich tomato-based curry", "price": 16.99, "category": "Non-Veg", "image": "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400&h=300&fit=crop&crop=center"},

    # Kebabs & Tandoor
    {"id": 11, "name": "Seekh Kebab", "description": "Spiced minced mutton grilled on skewers", "price": 14.99, "category": "Kebabs", "image": "https://tse4.mm.bing.net/th/id/OIP.WrAOvoxSRA7nG2Gzu42pXwAAAA?rs=1&pid=ImgDetMain&o=7&rm=3"},
    {"id": 12, "name": "Chicken Tikka", "description": "Marinated chicken chunks grilled in tandoor", "price": 15.99, "category": "Kebabs", "image": "https://images.saymedia-content.com/.image/t_share/MTg0Mzg1ODQ2OTk5OTE4MDU4/7-coloured-chicken-tikka-kebabs.jpg"},
    {"id": 13, "name": "Shammi Kebab", "description": "Soft, melt-in-mouth mutton patties with spices", "price": 13.99, "category": "Kebabs", "image": "https://images.unsplash.com/photo-1628294895950-9805252327bc?w=400&h=300&fit=crop&crop=center"},
    {"id": 14, "name": "Boti Kebab", "description": "Tender mutton pieces marinated and grilled to perfection", "price": 17.99, "category": "Kebabs", "image": "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop&crop=center"},
    {"id": 15, "name": "Fish Tikka", "description": "Fresh fish marinated in tandoori spices and grilled", "price": 16.99, "category": "Kebabs", "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400&h=300&fit=crop&crop=center"},

    # Vegetarian Delights
    {"id": 16, "name": "Paneer Butter Masala", "description": "Soft cottage cheese in rich tomato gravy", "price": 13.99, "category": "Vegetarian", "image": "https://www.cookwithmanali.com/wp-content/uploads/2019/05/Paneer-Butter-Masala-Recipe-400x606.jpg"},
    {"id": 17, "name": "Dal Hyderabadi", "description": "Traditional lentil curry with aromatic tempering", "price": 9.99, "category": "Vegetarian", "image": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400&h=300&fit=crop&crop=center"},
    {"id": 18, "name": "Bagara Baingan", "description": "Hyderabadi style stuffed eggplant curry", "price": 12.99, "category": "Vegetarian", "image": "https://th.bing.com/th/id/OIP.rGAncWkTNOGuGaal7jGP9wHaEK?w=326&h=183&c=7&r=0&o=7&pid=1.7&rm=3"},
    {"id": 19, "name": "Aloo Gosht Style Aloo", "description": "Spiced potatoes cooked in rich gravy", "price": 10.99, "category": "Vegetarian", "image": "https://i.ytimg.com/vi/aJEgjpja9c4/maxresdefault.jpg"},
    {"id": 20, "name": "Mixed Vegetable Curry", "description": "Seasonal vegetables in aromatic Hyderabadi spices", "price": 11.99, "category": "Vegetarian", "image": "https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400&h=300&fit=crop&crop=center"},

    # Rice & Breads
    {"id": 21, "name": "Hyderabadi Pulao", "description": "Fragrant rice cooked with whole spices and ghee", "price": 8.99, "category": "Rice", "image": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=400&h=300&fit=crop&crop=center"},
    {"id": 22, "name": "Roomali Roti", "description": "Paper-thin handkerchief bread, soft and delicate", "price": 3.99, "category": "Breads", "image": "https://www.cookwithkushi.com/wp-content/uploads/2016/10/rumali_roti_roomali_roti_recipe.jpg"},
    {"id": 23, "name": "Hyderabadi Naan", "description": "Soft leavened bread baked in tandoor", "price": 4.99, "category": "Breads", "image": "https://www.awesomecuisine.com/wp-content/uploads/2017/08/hyderabadi_naan.jpg"},
    {"id": 24, "name": "Kulcha", "description": "Stuffed bread with spiced filling", "price": 5.99, "category": "Breads", "image": "https://www.ruchiskitchen.com/wp-content/uploads/2014/11/Wheat-Kulcha-recipe-1.jpg.webp"},

    # Desserts
    {"id": 25, "name": "Double Ka Meetha", "description": "Hyderabadi bread pudding with nuts and saffron", "price": 7.99, "category": "Desserts", "image": "https://www.nuaodisha.com/Receipe/Double-ka-Meetha-1-Double-ka-meetha.jpg"},
    {"id": 26, "name": "Khubani Ka Meetha", "description": "Apricot dessert with cream, a Hyderabadi specialty", "price": 8.99, "category": "Desserts", "image": "https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=300&fit=crop&crop=center"},
    {"id": 27, "name": "Sheer Khurma", "description": "Vermicelli pudding with dates and nuts", "price": 6.99, "category": "Desserts", "image": "https://mytastycurry.com/wp-content/uploads/2018/05/Sheer-Khurma1-.jpg"},
    {"id": 28, "name": "Qubani Ka Meetha with Ice Cream", "description": "Traditional apricot dessert served with vanilla ice cream", "price": 9.99, "category": "Desserts", "image": "https://www.yummyfoodrecipes.com/resources/picture/org/Khubani-ka-meetha.jpg"},
    {"id": 29, "name": "Kulfi Falooda", "description": "Traditional Indian ice cream with vermicelli and rose syrup", "price": 7.99, "category": "Desserts", "image": "https://tse2.mm.bing.net/th/id/OIP.0G7Cot9fAGA8BseLVTskRgAAAA?rs=1&pid=ImgDetMain&o=7&rm=3"},
    {"id": 30, "name": "Gulab Jamun", "description": "Soft milk dumplings in cardamom flavored syrup", "price": 5.99, "category": "Desserts", "image": "https://th.bing.com/th/id/OIP.TR6gVZG-S4YxWTyGXxAHiwHaFk?w=256&h=192&c=7&r=0&o=7&pid=1.7&rm=3"},

    # Beverages
    {"id": 31, "name": "Hyderabadi Chai", "description": "Traditional spiced tea with cardamom and ginger", "price": 2.99, "category": "Beverages", "image": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=400&h=300&fit=crop&crop=center"},
    {"id": 32, "name": "Lassi", "description": "Refreshing yogurt drink, sweet or salted", "price": 4.99, "category": "Beverages", "image": "https://www.indianhealthyrecipes.com/wp-content/uploads/2022/03/lassi-recipe.jpg"},
    {"id": 33, "name": "Fresh Lime Water", "description": "Refreshing lime juice with mint and spices", "price": 3.99, "category": "Beverages", "image": "https://cdn.grofers.com/assets/search/usecase/banner/fresh_lime_water_01.png"}
]

def generate_verification_token():
    """Generate a random verification token"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

@app.route('/')
def index():
    """Landing page - redirect based on authentication status"""
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            phone = request.form.get('phone', '').strip()
            
            # Validation
            if not all([username, email, password, first_name, last_name]):
                flash('All fields except phone are required.', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('register.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
                return render_template('register.html')
            
            # Check if user already exists
            from db_models import User
            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'error')
                return render_template('register.html')
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered.', 'error')
                return render_template('register.html')
            
            # Create new user
            verification_token = generate_verification_token()
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                verification_token=verification_token,
                is_verified=True  # Setting to True since we don't have email service
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    
    if request.method == 'POST':
        try:
            username_or_email = request.form.get('username_or_email', '').strip()
            password = request.form.get('password', '')
            remember_me = bool(request.form.get('remember_me'))
            
            if not username_or_email or not password:
                flash('Please enter both username/email and password.', 'error')
                return render_template('login.html')
            
            # Find user by username or email
            from db_models import User
            user = User.query.filter(
                (User.username == username_or_email) | 
                (User.email == username_or_email.lower())
            ).first()
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user, remember=remember_me)
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.first_name}!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('menu'))
            else:
                flash('Invalid username/email or password.', 'error')
                
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/menu')
@login_required
def menu():
    """Display the food menu page"""
    return render_template('menu.html', menu_items=MENU_ITEMS)

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    """Handle order placement"""
    try:
        # Get selected items from form
        selected_items = request.form.getlist('items')
        quantities = {}
        
        # Get quantities for each selected item
        for item_id in selected_items:
            quantity_key = f'quantity_{item_id}'
            quantity = int(request.form.get(quantity_key, 1))
            quantities[int(item_id)] = quantity
        
        if not selected_items:
            flash('Please select at least one item to order.', 'warning')
            return redirect(url_for('menu'))
        
        # Calculate total and prepare order items
        total_price = 0
        order_items_data = []
        
        for item_id in selected_items:
            item_id = int(item_id)
            quantity = quantities[item_id]
            
            # Find the menu item
            menu_item = next((item for item in MENU_ITEMS if item['id'] == item_id), None)
            if menu_item:
                item_total = menu_item['price'] * quantity
                total_price += item_total
                order_items_data.append({
                    'item_id': item_id,
                    'name': menu_item['name'],
                    'price': menu_item['price'],
                    'quantity': quantity,
                    'total': item_total
                })
        
        # Create new order
        from db_models import Order, OrderItem
        
        order = Order(
            user_id=current_user.id,
            total_amount=total_price,
            order_date=datetime.utcnow()
        )
        db.session.add(order)
        db.session.flush()  # To get the order ID
        
        # Add order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                item_id=item_data['item_id'],
                item_name=item_data['name'],
                item_price=item_data['price'],
                quantity=item_data['quantity'],
                total_price=item_data['total']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        flash(f'Order #{order.id} placed successfully! Total: ${total_price:.2f}', 'success')
        return redirect(url_for('orders'))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error placing order: {str(e)}")
        flash('An error occurred while placing your order. Please try again.', 'error')
        return redirect(url_for('menu'))

@app.route('/orders')
@login_required
def orders():
    """Display order history"""
    try:
        from db_models import Order, OrderItem
        
        # Get user's orders with their items
        orders = db.session.query(Order).filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
        
        # Get order items for each order
        orders_with_items = []
        for order in orders:
            order_items = db.session.query(OrderItem).filter_by(order_id=order.id).all()
            orders_with_items.append({
                'order': order,
                'items': order_items
            })
        
        return render_template('orders.html', orders_with_items=orders_with_items)
        
    except Exception as e:
        app.logger.error(f"Error fetching orders: {str(e)}")
        flash('An error occurred while fetching orders.', 'error')
        return render_template('orders.html', orders_with_items=[])

# Gemini AI Integration
@app.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chatbot conversations"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({'response': 'Please send a message.'})
        import google.generativeai as genai
        genai.configure(api_key="AIzaSyAHCaoLAV-n0Rszbw4DnwJI4GrYHflfvcE")
        model_names = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.0-pro", "gemini-pro"]
        menu_context = """You are Pavan, the expert chef and AI assistant at Pavan's Bawarchi, a premium Hyderabadi restaurant.\n\nOur Specialties:\n🍛 BIRYANIS: Authentic Hyderabadi dum biryanis including Chicken, Mutton, Fish, Prawn, and Vegetable\n🍖 HYDERABADI CLASSICS: Mutton Marag, Chicken Haleem, Keema Kaleji, Chicken Korma\n🥘 KEBABS & TANDOOR: Seekh Kebab, Shammi Kebab, Boti Kebab, Chicken/Fish Tikka\n🥗 VEGETARIAN: Paneer specialties, Dal Hyderabadi, Bagara Baingan\n🍞 BREADS: Roomali Roti, Hyderabadi Naan, Kulcha\n🍰 DESSERTS: Double Ka Meetha, Khubani Ka Meetha, Sheer Khurma, Kulfi Falooda\n☕ BEVERAGES: Hyderabadi Chai, Lassi, Fresh Lime Water\n\nALWAYS start by asking about their mood or preferences if they haven't mentioned any. Based on their mood/preferences, recommend specific dishes from our menu. Be warm, knowledgeable about Hyderabadi cuisine, and suggest dishes that match their current feeling or craving.\n\nExamples:\n- If happy/celebrating: Recommend our premium Mutton Biryani or special kebab platters\n- If comfort-seeking: Suggest Chicken Haleem or Double Ka Meetha\n- If spicy/adventurous: Recommend spiced dishes like Keema Kaleji or Seekh Kebab\n- If light/healthy: Suggest Dal Hyderabadi with breads or vegetable dishes\n\nCurrent user message: """
        prompt = f"{menu_context}\n\nUser question: {user_message}\n\nPlease respond in a helpful, friendly manner and recommend specific dishes from our menu when appropriate."
        last_exception = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                ai_response = response.text if hasattr(response, 'text') and response.text else None
                if ai_response:
                    return jsonify({'response': ai_response})
            except Exception as model_exc:
                last_exception = model_exc
                import traceback
                app.logger.error(f"Gemini API error with model {model_name}: {model_exc}\n{traceback.format_exc()}")
        # If all models fail, show the last error for debugging
        return jsonify({'response': f'Gemini API error: {last_exception}'})
    except Exception as e:
        import traceback
        app.logger.error(f"Chat error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'response': f'Internal error: {str(e)}'})

# Initialize database
with app.app_context():
    # Import models to ensure tables are created
    from db_models import User, Order, OrderItem
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


# import os
# import logging
# import json
# import secrets
# import string
# from datetime import datetime

# from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.orm import DeclarativeBase
# from werkzeug.middleware.proxy_fix import ProxyFix
# from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# # Logging
# logging.basicConfig(level=logging.DEBUG)

# # SQLAlchemy base
# class Base(DeclarativeBase):
#     pass

# db = SQLAlchemy(model_class=Base)

# # Flask app
# app = Flask(__name__)
# app.secret_key = "dev-secret-key-change-in-production"
# app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# # Database config
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///orders.db"
# app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
#     "pool_recycle": 300,
#     "pool_pre_ping": True,
# }

# db.init_app(app)

# # Login Manager
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'

# @login_manager.user_loader
# def load_user(user_id):
#     from models import User
#     return User.query.get(int(user_id))

# # === Menu (full data restored) ===
# MENU_ITEMS = [
#     {"id": 1, "name": "Hyderabadi Chicken Biryani", "description": "Authentic Hyderabadi dum biryani with tender chicken and aromatic basmati rice", "price": 18.99, "category": "Biryani", "image": "https://images.unsplash.com/photo-1563379091339-03246962d51d?w=400&h=300&fit=crop&crop=center"},
#     {"id": 2, "name": "Mutton Biryani", "description": "Premium mutton pieces cooked with fragrant spices and saffron rice", "price": 22.99, "category": "Biryani", "image": "https://kitchenofdebjani.com/wp-content/uploads/2018/10/Royal-Indian-Hotel-Mutton-Biryani.jpg"},
#     {"id": 3, "name": "Hyderabadi Vegetable Biryani", "description": "Mixed vegetables layered with aromatic basmati rice and dum cooked", "price": 15.99, "category": "Biryani", "image": "https://th.bing.com/th/id/OIP.mqsjhI7s7syKm5lN5IPGdAHaEK?w=272&h=180&c=7&r=0&o=7&pid=1.7&rm=3"},
#     {"id": 4, "name": "Fish Biryani", "description": "Fresh fish marinated in spices and cooked with fragrant rice", "price": 19.99, "category": "Biryani", "image": "https://as2.ftcdn.net/v2/jpg/04/18/22/51/1000_F_418225117_RHkXwPGZ20Ajrzzad59nGIidLY9vhj6y.jpg"},
#     {"id": 5, "name": "Prawn Biryani", "description": "Succulent prawns with aromatic spices and basmati rice", "price": 21.99, "category": "Biryani", "image": "https://i.ytimg.com/vi/yUntK4Vdqfw/maxresdefault.jpg"},

#     # Hyderabadi Non-Veg Specials
#     {"id": 6, "name": "Mutton Marag", "description": "Traditional Hyderabadi mutton curry with rich, flavorful gravy", "price": 20.99, "category": "Non-Veg", "image": "https://wirally.com/wp-content/uploads/2023/03/Best-Mutton-Marag-In-Hyderabad1-696x392.jpg"},
#     {"id": 7, "name": "Chicken Haleem", "description": "Slow-cooked lentils with tender chicken, a Hyderabadi favorite", "price": 16.99, "category": "Non-Veg", "image": "https://www.thedeliciouscrescent.com/wp-content/uploads/2020/08/Haleem-4.jpg"},
#     {"id": 8, "name": "Hyderabadi Chicken Korma", "description": "Creamy chicken curry with cashews and aromatic spices", "price": 17.99, "category": "Non-Veg", "image": "https://th.bing.com/th/id/OIP.EsGHsvXoydIiinWXHvkJ5AHaE8?w=301&h=200&c=7&r=0&o=7&pid=1.7&rm=3"},
#     {"id": 9, "name": "Keema Kaleji", "description": "Spiced minced mutton with liver, cooked Hyderabadi style", "price": 18.99, "category": "Non-Veg", "image": "https://i.pinimg.com/736x/48/3a/ea/483aeafedff00d056ecbb32b29c55d33.jpg"},
#     {"id": 10, "name": "Chicken Tikka Masala", "description": "Tandoor grilled chicken in rich tomato-based curry", "price": 16.99, "category": "Non-Veg", "image": "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400&h=300&fit=crop&crop=center"},

#     # Kebabs & Tandoor
#     {"id": 11, "name": "Seekh Kebab", "description": "Spiced minced mutton grilled on skewers", "price": 14.99, "category": "Kebabs", "image": "https://tse4.mm.bing.net/th/id/OIP.WrAOvoxSRA7nG2Gzu42pXwAAAA?rs=1&pid=ImgDetMain&o=7&rm=3"},
#     {"id": 12, "name": "Chicken Tikka", "description": "Marinated chicken chunks grilled in tandoor", "price": 15.99, "category": "Kebabs", "image": "https://images.saymedia-content.com/.image/t_share/MTg0Mzg1ODQ2OTk5OTE4MDU4/7-coloured-chicken-tikka-kebabs.jpg"},
#     {"id": 13, "name": "Shammi Kebab", "description": "Soft, melt-in-mouth mutton patties with spices", "price": 13.99, "category": "Kebabs", "image": "https://images.unsplash.com/photo-1628294895950-9805252327bc?w=400&h=300&fit=crop&crop=center"},
#     {"id": 14, "name": "Boti Kebab", "description": "Tender mutton pieces marinated and grilled to perfection", "price": 17.99, "category": "Kebabs", "image": "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop&crop=center"},
#     {"id": 15, "name": "Fish Tikka", "description": "Fresh fish marinated in tandoori spices and grilled", "price": 16.99, "category": "Kebabs", "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400&h=300&fit=crop&crop=center"},

#     # Vegetarian Delights
#     {"id": 16, "name": "Paneer Butter Masala", "description": "Soft cottage cheese in rich tomato gravy", "price": 13.99, "category": "Vegetarian", "image": "https://www.cookwithmanali.com/wp-content/uploads/2019/05/Paneer-Butter-Masala-Recipe-400x606.jpg"},
#     {"id": 17, "name": "Dal Hyderabadi", "description": "Traditional lentil curry with aromatic tempering", "price": 9.99, "category": "Vegetarian", "image": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400&h=300&fit=crop&crop=center"},
#     {"id": 18, "name": "Bagara Baingan", "description": "Hyderabadi style stuffed eggplant curry", "price": 12.99, "category": "Vegetarian", "image": "https://th.bing.com/th/id/OIP.rGAncWkTNOGuGaal7jGP9wHaEK?w=326&h=183&c=7&r=0&o=7&pid=1.7&rm=3"},
#     {"id": 19, "name": "Aloo Gosht Style Aloo", "description": "Spiced potatoes cooked in rich gravy", "price": 10.99, "category": "Vegetarian", "image": "https://i.ytimg.com/vi/aJEgjpja9c4/maxresdefault.jpg"},
#     {"id": 20, "name": "Mixed Vegetable Curry", "description": "Seasonal vegetables in aromatic Hyderabadi spices", "price": 11.99, "category": "Vegetarian", "image": "https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400&h=300&fit=crop&crop=center"},

#     # Rice & Breads
#     {"id": 21, "name": "Hyderabadi Pulao", "description": "Fragrant rice cooked with whole spices and ghee", "price": 8.99, "category": "Rice", "image": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=400&h=300&fit=crop&crop=center"},
#     {"id": 22, "name": "Roomali Roti", "description": "Paper-thin handkerchief bread, soft and delicate", "price": 3.99, "category": "Breads", "image": "https://www.cookwithkushi.com/wp-content/uploads/2016/10/rumali_roti_roomali_roti_recipe.jpg"},
#     {"id": 23, "name": "Hyderabadi Naan", "description": "Soft leavened bread baked in tandoor", "price": 4.99, "category": "Breads", "image": "https://www.awesomecuisine.com/wp-content/uploads/2017/08/hyderabadi_naan.jpg"},
#     {"id": 24, "name": "Kulcha", "description": "Stuffed bread with spiced filling", "price": 5.99, "category": "Breads", "image": "https://www.ruchiskitchen.com/wp-content/uploads/2014/11/Wheat-Kulcha-recipe-1.jpg.webp"},

#     # Desserts
#     {"id": 25, "name": "Double Ka Meetha", "description": "Hyderabadi bread pudding with nuts and saffron", "price": 7.99, "category": "Desserts", "image": "https://www.nuaodisha.com/Receipe/Double-ka-Meetha-1-Double-ka-meetha.jpg"},
#     {"id": 26, "name": "Khubani Ka Meetha", "description": "Apricot dessert with cream, a Hyderabadi specialty", "price": 8.99, "category": "Desserts", "image": "https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=300&fit=crop&crop=center"},
#     {"id": 27, "name": "Sheer Khurma", "description": "Vermicelli pudding with dates and nuts", "price": 6.99, "category": "Desserts", "image": "https://mytastycurry.com/wp-content/uploads/2018/05/Sheer-Khurma1-.jpg"},
#     {"id": 28, "name": "Qubani Ka Meetha with Ice Cream", "description": "Traditional apricot dessert served with vanilla ice cream", "price": 9.99, "category": "Desserts", "image": "https://www.yummyfoodrecipes.com/resources/picture/org/Khubani-ka-meetha.jpg"},
#     {"id": 29, "name": "Kulfi Falooda", "description": "Traditional Indian ice cream with vermicelli and rose syrup", "price": 7.99, "category": "Desserts", "image": "https://tse2.mm.bing.net/th/id/OIP.0G7Cot9fAGA8BseLVTskRgAAAA?rs=1&pid=ImgDetMain&o=7&rm=3"},
#     {"id": 30, "name": "Gulab Jamun", "description": "Soft milk dumplings in cardamom flavored syrup", "price": 5.99, "category": "Desserts", "image": "https://th.bing.com/th/id/OIP.TR6gVZG-S4YxWTyGXxAHiwHaFk?w=256&h=192&c=7&r=0&o=7&pid=1.7&rm=3"},

#     # Beverages
#     {"id": 31, "name": "Hyderabadi Chai", "description": "Traditional spiced tea with cardamom and ginger", "price": 2.99, "category": "Beverages", "image": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=400&h=300&fit=crop&crop=center"},
#     {"id": 32, "name": "Lassi", "description": "Refreshing yogurt drink, sweet or salted", "price": 4.99, "category": "Beverages", "image": "https://www.indianhealthyrecipes.com/wp-content/uploads/2022/03/lassi-recipe.jpg"},
#     {"id": 33, "name": "Fresh Lime Water", "description": "Refreshing lime juice with mint and spices", "price": 3.99, "category": "Beverages", "image": "https://cdn.grofers.com/assets/search/usecase/banner/fresh_lime_water_01.png"}
# ]

# # === Helpers ===
# def generate_verification_token():
#     return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

# # === Routes ===
# @app.route('/')
# def index():
#     if current_user.is_authenticated:
#         return redirect(url_for('menu'))
#     return render_template('landing.html')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('menu'))

#     if request.method == 'POST':
#         try:
#             username = request.form.get('username', '').strip()
#             email = request.form.get('email', '').strip().lower()
#             password = request.form.get('password', '')
#             confirm_password = request.form.get('confirm_password', '')
#             first_name = request.form.get('first_name', '').strip()
#             last_name = request.form.get('last_name', '').strip()
#             phone = request.form.get('phone', '').strip()

#             if not all([username, email, password, first_name, last_name]):
#                 flash('All fields except phone are required.', 'error')
#                 return render_template('register.html')

#             if password != confirm_password:
#                 flash('Passwords do not match.', 'error')
#                 return render_template('register.html')

#             if len(password) < 6:
#                 flash('Password must be at least 6 characters.', 'error')
#                 return render_template('register.html')

#             from models import User
#             if User.query.filter_by(username=username).first():
#                 flash('Username already exists.', 'error')
#                 return render_template('register.html')
#             if User.query.filter_by(email=email).first():
#                 flash('Email already registered.', 'error')
#                 return render_template('register.html')

#             user = User(
#                 username=username,
#                 email=email,
#                 password_hash=generate_password_hash(password),
#                 first_name=first_name,
#                 last_name=last_name,
#                 phone=phone,
#                 verification_token=generate_verification_token(),
#                 is_verified=True
#             )

#             db.session.add(user)
#             db.session.commit()

#             flash('Registration successful! You can now log in.', 'success')
#             return redirect(url_for('login'))

#         except Exception as e:
#             db.session.rollback()
#             app.logger.error(f"Registration error: {str(e)}")
#             flash('Error during registration.', 'error')

#     return render_template('register.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('menu'))

#     if request.method == 'POST':
#         try:
#             username_or_email = request.form.get('username_or_email', '').strip()
#             password = request.form.get('password', '')
#             remember_me = bool(request.form.get('remember_me'))

#             if not username_or_email or not password:
#                 flash('Please enter both username/email and password.', 'error')
#                 return render_template('login.html')

#             from models import User
#             user = User.query.filter(
#                 (User.username == username_or_email) |
#                 (User.email == username_or_email.lower())
#             ).first()

#             if user and check_password_hash(user.password_hash, password):
#                 login_user(user, remember=remember_me)
#                 next_page = request.args.get('next')
#                 flash(f'Welcome back, {user.first_name}!', 'success')
#                 return redirect(next_page) if next_page else redirect(url_for('menu'))
#             else:
#                 flash('Invalid username/email or password.', 'error')

#         except Exception as e:
#             app.logger.error(f"Login error: {str(e)}")
#             flash('Login failed. Try again.', 'error')

#     return render_template('login.html')

# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     flash('Logged out successfully.', 'info')
#     return redirect(url_for('index'))

# @app.route('/menu')
# @login_required
# def menu():
#     return render_template('menu.html', menu_items=MENU_ITEMS)

# @app.route('/place_order', methods=['POST'])
# @login_required
# def place_order():
#     try:
#         selected_items = request.form.getlist('items')
#         quantities = {}

#         for item_id in selected_items:
#             quantity_key = f'quantity_{item_id}'
#             quantity = int(request.form.get(quantity_key, 1))
#             quantities[int(item_id)] = quantity

#         if not selected_items:
#             flash('Please select at least one item.', 'warning')
#             return redirect(url_for('menu'))

#         total_price = 0
#         order_items_data = []

#         for item_id in selected_items:
#             item_id = int(item_id)
#             quantity = quantities[item_id]
#             menu_item = next((item for item in MENU_ITEMS if item['id'] == item_id), None)
#             if menu_item:
#                 item_total = menu_item['price'] * quantity
#                 total_price += item_total
#                 order_items_data.append({
#                     'item_id': item_id,
#                     'name': menu_item['name'],
#                     'price': menu_item['price'],
#                     'quantity': quantity,
#                     'total': item_total
#                 })

#         from models import Order, OrderItem
#         order = Order(user_id=current_user.id, total_amount=total_price, order_date=datetime.utcnow())
#         db.session.add(order)
#         db.session.flush()

#         for item_data in order_items_data:
#             order_item = OrderItem(
#                 order_id=order.id,
#                 item_id=item_data['item_id'],
#                 item_name=item_data['name'],
#                 item_price=item_data['price'],
#                 quantity=item_data['quantity'],
#                 total_price=item_data['total']
#             )
#             db.session.add(order_item)

#         db.session.commit()

#         flash(f'Order #{order.id} placed! Total: ${total_price:.2f}', 'success')
#         return redirect(url_for('orders'))

#     except Exception as e:
#         db.session.rollback()
#         app.logger.error(f"Order error: {str(e)}")
#         flash('Could not place order.', 'error')
#         return redirect(url_for('menu'))

# @app.route('/orders')
# @login_required
# def orders():
#     try:
#         from models import Order, OrderItem
#         orders = db.session.query(Order).filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()

#         orders_with_items = []
#         for order in orders:
#             order_items = db.session.query(OrderItem).filter_by(order_id=order.id).all()
#             orders_with_items.append({'order': order, 'items': order_items})

#         return render_template('orders.html', orders_with_items=orders_with_items)

#     except Exception as e:
#         app.logger.error(f"Fetch orders error: {str(e)}")
#         flash('Could not load orders.', 'error')
#         return render_template('orders.html', orders_with_items=[])

# # ✅ Chatbot with Gemini API Key
# @app.route('/chat', methods=['POST'])
# @login_required
# def chat():
#     try:
#         data = request.get_json()
#         user_message = data.get('message', '')

#         if not user_message:
#             return jsonify({'response': 'Please send a message.'})

#         import google.generativeai as genai
#         genai.configure(api_key="AIzaSyAHCaoLAV-n0Rszbw4DnwJI4GrYHflfvcE")
#         # Try both model names for compatibility
#         model_names = ['gemini-1.5-flash', 'gemini-1.0-pro', 'gemini-pro']
#         menu_context = """You are Pavan, an expert chef at Pavan's Bawarchi (Hyderabadi Restaurant).\n\nSuggest dishes warmly based on the user's mood:\n- Celebrating → Mutton Biryani, Kebabs\n- Comfort → Haleem, Double Ka Meetha\n- Light → Dal, Roomali Roti\n- Spicy → Keema Kaleji, Seekh Kebab\n"""
#         prompt = f"{menu_context}\n\nUser: {user_message}\n\nAssistant:"
#         last_exception = None
#         for model_name in model_names:
#             try:
#                 model = genai.GenerativeModel(model_name)
#                 response = model.generate_content(prompt)
#                 ai_response = response.text.strip() if hasattr(response, 'text') and response.text else None
#                 if ai_response:
#                     return jsonify({'response': ai_response})
#             except Exception as model_exc:
#                 last_exception = model_exc
#                 app.logger.error(f"Gemini API error with model {model_name}: {model_exc}")
#         # If all models fail
#         app.logger.error(f"All Gemini model attempts failed. Last error: {last_exception}")
#         return jsonify({'response': 'AI assistant is currently unavailable. Please contact support.'})
#     except Exception as e:
#         import traceback
#         app.logger.error(f"Chat error: {str(e)}\n{traceback.format_exc()}")
#         return jsonify({'response': 'Something went wrong. Try again later.'})

# # DB init
# with app.app_context():
#     from models import User, Order, OrderItem
#     db.create_all()

# # Run the app
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)
# # import os