from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from marshmallow import ValidationError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Tuckerstriker12@localhost/e_commerce'
db = SQLAlchemy(app)
ma = Marshmallow(app)

class CustomerSchema(ma.Schema):
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ('name', 'email', 'phone', 'id')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

class AccountSchema(ma.Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)

    class Meta:
        fields = ('username', 'password', 'id', 'customer_id')

account_schema = AccountSchema()
accounts_schema = AccountSchema(many=True)

class ProductSchema(ma.Schema):
    name = fields.String(required=True)
    price = fields.Float(required=True)

    class Meta:
        fields = ('name', 'price', 'id')

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

class OrderSchema(ma.Schema):
    date = fields.Date(required=True)
    expected_delivery = fields.Date(required=False)
    status = fields.String(required=True)
    customer_id = fields.Integer(required=True)
    products = fields.List(fields.Nested(ProductSchema))


    class Meta:
        fields = ('id','date','expected_delivery','status','customer_id','products')

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

class Customer(db.Model):
    __tablename__ = 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320))
    phone = db.Column(db.String(15))
    orders = db.relationship('Order', backref='customer')

class CustomerAccount(db.Model):
    __tablename__ = 'Customer_Accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    customer = db.relationship('Customer', backref='customer_account', uselist=False)

order_product = db.Table('Order_Product',
    db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('Products.id'), primary_key=True)
)

class Order(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    expected_delivery_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Pending')
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    products = db.relationship('Product', secondary=order_product, backref=db.backref('orders_associations', lazy='dynamic'))

class Product(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)

#Task 1: Customer and Customer Account Management

@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)

@app.route('/customers/<int:id>', methods=['GET'])
def get_customer_by_id(id):
    try:
        customer = Customer.query.get_or_404(id)
    except ValidationError as e:
        return jsonify(e.messages), 400
    return customer_schema.jsonify(customer)
    

@app.route('/customers', methods=['POST'])
def add_customers():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], phone=customer_data['phone'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message':'A new customer has been added!'}), 201

@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.phone = customer_data['phone']
    db.session.commit()
    return jsonify({'message':'The customer has been successfully updated!'}), 200

@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message':'The specificed customer has been deleted'}), 200

@app.route('/Customer_Accounts/<int:id>', methods=['GET'])
def get_customer_account_by_id(id):
    try:
        customer_account = CustomerAccount.query.get_or_404(id)
    except ValidationError as e:
        return jsonify(e.messages), 400
    return account_schema.jsonify(customer_account)

@app.route('/Customer_Accounts', methods=['GET'])
def get_customers_accounts():
    accounts = CustomerAccount.query.all()
    return accounts_schema.jsonify(accounts)

@app.route('/Customer_Accounts', methods=['POST'])
def create_account():
    try:
        account_data = account_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_account = CustomerAccount(username=account_data['username'], password=account_data['password'])
    db.session.add(new_account)
    db.session.commit()
    return jsonify({'message':'A new account has been created!'}), 201

@app.route('/Customer_Accounts/<int:id>', methods=['PUT'])
def update_account(id):
    account = CustomerAccount.query.get_or_404(id)
    try:
        account_data = account_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    account.username = account_data['username']
    account.password = account_data['password']
    db.session.commit()
    return jsonify({'messages':'The account information has been updated!'})

@app.route('/Customer_Accounts/<int:id>', methods=['DELETE'])
def delete_account(id):
    account = CustomerAccount.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({'message':'The Account with the specificed ID has been deleted!'})

#Task 2: Product Catalog

@app.route('/Products', methods=['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Product(name=product_data['name'],price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message':'A new product has been added!'})

@app.route('/Products/<int:id>', methods=['GET'])
def find_product_by_id(id):
    try:
        product = Product.query.get_or_404(id)
    except ValidationError as e:
        return jsonify(e.messages), 400
    return product_schema.jsonify(product)

@app.route('/Products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.name = product_data['name']
    product.price = product_data['price']

    db.session.commit()
    return jsonify({'message':'The product and its price have been updated!'})

@app.route('/Products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message':'The product has been deleted!'})

@app.route('/Products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

#Task 3:Order Processing

@app.route('/Orders', methods=['POST'])
def place_order():
    try:
        data = request.json
        customer_id = data.get('customer_id')
        product_ids = data.get('product_ids')

        if not customer_id or not product_ids:
            return jsonify({'message':'Customer ID and Product ID/s are required'}), 400
        
        # Ensure product_ids is a list
        if not isinstance(product_ids, list):
            return jsonify({'message': 'Product IDs must be a list'}), 400
        
        # Debugging statement to print product_ids
        print(f"Product IDs: {product_ids}")

        # Check if the list is not empty
        if len(product_ids) == 0:
            return jsonify({'message': 'Product ID list cannot be empty'}), 400

        customer = Customer.query.get_or_404(customer_id)
        products = Product.query.filter(Product.id.in_(product_ids)).all()

        if not products:
            return jsonify({'message':'No valid products found'}), 400
        
        new_order = Order(
            date=data.get('date'),
            expected_delivery_date=data.get('expected_delivery_date'), 
            status=data.get('status', 'Pending'),
            customer_id=customer.id
        )
        new_order.products.extend(products)

        db.session.add(new_order)
        db.session.commit()

        return order_schema.jsonify(new_order), 201
    except ValidationError as e:
        return jsonify(e.messages), 400
    except Exception as e:
        # Catch any other exceptions and return a 500 error
        return jsonify({'message': 'Internal server error', 'error': str(e)}), 500
    
@app.route('/Orders/<int:id>', methods=['GET'])
def retrieve_order(id):
    order = Order.query.get_or_404(id)
    return order_schema.jsonify(order), 200

@app.route('/Orders/<int:id>/track', methods=['GET'])
def track_order(id):
    order = Order.query.get_or_404(id)
    tracking_info = {
        'order_date': order.date,
        'exepected_delivery_date': order.expected_delivery_date,
        'status': order.status,
        'products': products_schema.dump(order.products)
    }
    return jsonify(tracking_info), 200




with app.app_context():
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)