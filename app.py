import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime

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

# Food menu data
MENU_ITEMS = [
    {"id": 1, "name": "Classic Burger", "description": "Beef patty with lettuce, tomato, and cheese", "price": 12.99},
    {"id": 2, "name": "Chicken Sandwich", "description": "Grilled chicken breast with mayo and pickles", "price": 10.99},
    {"id": 3, "name": "Margherita Pizza", "description": "Fresh mozzarella, tomato sauce, and basil", "price": 14.99},
    {"id": 4, "name": "Caesar Salad", "description": "Romaine lettuce with parmesan and croutons", "price": 8.99},
    {"id": 5, "name": "Fish & Chips", "description": "Beer-battered cod with crispy fries", "price": 15.99},
    {"id": 6, "name": "Pasta Carbonara", "description": "Creamy pasta with bacon and parmesan", "price": 13.99},
    {"id": 7, "name": "Veggie Wrap", "description": "Fresh vegetables with hummus in a tortilla", "price": 9.99},
    {"id": 8, "name": "BBQ Ribs", "description": "Slow-cooked ribs with barbecue sauce", "price": 18.99},
    {"id": 9, "name": "Chicken Wings", "description": "Spicy buffalo wings with ranch dip", "price": 11.99},
    {"id": 10, "name": "Chocolate Cake", "description": "Rich chocolate cake with vanilla ice cream", "price": 6.99}
]

@app.route('/')
def menu():
    """Display the food menu page"""
    return render_template('menu.html', menu_items=MENU_ITEMS)

@app.route('/place_order', methods=['POST'])
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
        from models import Order, OrderItem
        
        order = Order(
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
def orders():
    """Display order history"""
    try:
        from models import Order, OrderItem
        
        # Get all orders with their items
        orders = db.session.query(Order).order_by(Order.order_date.desc()).all()
        
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

# Initialize database
with app.app_context():
    # Import models to ensure tables are created
    from models import Order, OrderItem
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
