from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


# =======================
# DATABASE MODEL
# =======================

#user database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(20))
    theme = db.Column(db.String(20), default="dark")
    is_premium = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

#product database
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(300))
    affiliate_link = db.Column(db.String(500))
    description = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


# =======================
# ROUTES
# =======================


#admin routes protection
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


#admin dashboard routes
@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    products = Product.query.all()

    total_users = User.query.count()
    premium_users = User.query.filter_by(is_premium=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()
    total_products = Product.query.count()

    return render_template(
        "admin.html",
        users=users,
        products=products,
        total_users=total_users,
        premium_users=premium_users,
        admin_users=admin_users,
        total_products=total_products
    )


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/shopping")
def shopping():
    query = request.args.get("search")
    
    if query:
        products = Product.query.filter(Product.name.contains(query)).all()
    else:
        products = Product.query.all()

    return render_template("shopping.html", products=products)


@app.route("/premium")
@login_required
def premium():
    if not current_user.is_premium:
        return render_template("premium.html", locked=True)
    return render_template("premium.html", locked=False)


@app.route("/add-product", methods=["GET", "POST"])
@login_required
@admin_required
def add_product():
    if request.method == "POST":
        new_product = Product(
            name=request.form.get("name"),
            price=request.form.get("price"),
            image=request.form.get("image"),
            affiliate_link=request.form.get("affiliate_link"),
            description=request.form.get("description")
        )

        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for("admin_dashboard"))

    return render_template("add_product.html")


@app.route("/delete-product/<int:product_id>")
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/cart")
@login_required
def cart():
    cart_ids = session.get("cart", [])

    cart_items = Product.query.filter(Product.id.in_(cart_ids)).all()

    total = sum(item.price for item in cart_items)

    return render_template("cart.html", cart=cart_items, total=total)


@app.route("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):
    if "cart" not in session:
        session["cart"] = []

    session["cart"].append(product_id)
    session.modified = True

    return redirect(url_for("shopping"))


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", product=product)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        current_user.name = request.form.get("name")
        current_user.contact = request.form.get("contact")
        current_user.theme = request.form.get("theme")

        db.session.commit()
        return redirect(url_for("settings"))

    return render_template("settings.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            if user["email"] == "velloraenterprises@gmail.com":
                 user["is_admin"] = True
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/upgrade")
@login_required
def upgrade():
    current_user.is_premium = True
    db.session.commit()
    return redirect(url_for("premium"))

#promotion and depromotion routes
@app.route("/make-premium/<int:user_id>")
@login_required
@admin_required
def make_premium(user_id):
    user = User.query.get(user_id)
    user.is_premium = True
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/make-admin/<int:user_id>")
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get(user_id)
    user.is_admin = True
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/delete-user/<int:user_id>")
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user.id != current_user.id:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for("admin_dashboard"))

# =======================
# INIT DATABASE
# =======================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
