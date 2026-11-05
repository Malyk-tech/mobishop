import os
from pathlib import Path
from functools import wraps
from uuid import uuid4
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SHOPMOBI_SECRET", "development-only-change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
UPLOAD_FOLDER = Path(app.root_path) / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

# Temporary in-memory storage. Records reset when the app stops; uploaded images remain on disk.
merchants, products, orders, carts, favorites = [], [], [], {}, {}
next_merchant_id = next_product_id = next_order_id = 1
ADMIN_USERNAME = os.environ.get("SHOPMOBI_ADMIN", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get("SHOPMOBI_ADMIN_PASSWORD", "ChangeMe123!"))

CSS = r"""
:root{--bg:#f1f2ec;--surface:#fff;--surface2:#e7e9df;--text:#172018;--muted:#687267;--line:#dce1d7;--green:#173d2b;--green2:#2d6444;--accent:#a8c66c;--black:#080b09;--shadow:0 12px 35px rgba(18,40,24,.08)}
html[data-theme="dark"]{--bg:#111a14;--surface:#1b2820;--surface2:#26362a;--text:#f0f5ed;--muted:#b1beb0;--line:#344638;--green:#c0df9a;--green2:#a8d081;--accent:#b7d98a;--black:#070b08;--shadow:0 12px 35px rgba(0,0,0,.22)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;transition:background .2s,color .2s}a{color:inherit;text-decoration:none}button,input,select,textarea{font:inherit}button,.btn{border:0;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:11px 16px;border-radius:999px;background:var(--black);color:white;font-weight:650;text-decoration:none;transition:transform .15s,opacity .15s}button:hover,.btn:hover{opacity:.88;transform:translateY(-1px)}.btn-light{background:var(--surface2);color:var(--text)}.btn-green{background:var(--green);color:#fff}.btn-danger{background:#a82c2c;color:#fff}.icon-btn{width:42px;height:42px;padding:0;background:var(--surface);color:var(--text);border:1px solid var(--line);font-size:18px}.wrap{width:min(1180px,92%);margin:auto}.topbar{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--bg) 90%,transparent);backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}.nav{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:20px}.logo{font-size:25px;font-weight:900;letter-spacing:-1.3px;color:var(--green)}.logo span{color:var(--text)}.navlinks{display:flex;align-items:center;gap:20px;color:var(--muted);font-size:14px}.navlinks a:hover{color:var(--text)}.navactions{display:flex;gap:8px;align-items:center}.search{display:flex;align-items:center;gap:9px;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:0 15px;min-width:210px}.search input{border:0;outline:0;background:transparent;color:var(--text);padding:12px 0;width:100%}.hero{margin:30px auto 36px;border-radius:30px;overflow:hidden;min-height:350px;background:radial-gradient(circle at 85% 10%,#678b51 0,transparent 34%),linear-gradient(115deg,#102c1e,#315b38 58%,#8eaa6b);color:#fff;display:grid;grid-template-columns:1.1fr .9fr;align-items:center;padding:48px clamp(25px,5vw,70px);position:relative}.hero small{display:inline-block;background:#ffffff1f;border:1px solid #ffffff30;padding:8px 13px;border-radius:999px;letter-spacing:.08em;text-transform:uppercase;font-size:11px}.hero h1{font-size:clamp(38px,5vw,65px);line-height:.99;letter-spacing:-3px;max-width:560px;margin:22px 0 15px}.hero p{max-width:440px;color:#e2eadd;line-height:1.65}.hero .btn{background:#f5f6ee;color:#15271a;margin-top:10px}.hero-art{display:flex;justify-content:center;align-items:center;min-height:240px}.hero-art img{width:min(100%,400px);height:280px;object-fit:contain;filter:drop-shadow(0 25px 20px #06150b60)}.hero-placeholder{font-size:140px;filter:drop-shadow(0 20px 12px #06150b55)}.section-head{display:flex;justify-content:space-between;align-items:end;gap:14px;margin:32px 0 18px}.section-head h2{font-size:clamp(24px,3vw,32px);letter-spacing:-1px;margin:0}.section-head p{margin:7px 0 0;color:var(--muted)}.chips{display:flex;gap:9px;overflow-x:auto;padding:2px 0 8px;margin-bottom:15px}.chip{white-space:nowrap;border:1px solid var(--line);border-radius:999px;padding:10px 16px;background:var(--surface);color:var(--text);font-size:13px}.chip.active{background:var(--black);color:#fff;border-color:var(--black)}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px}.product-card{background:var(--surface);border:1px solid var(--line);border-radius:22px;padding:12px;min-width:0;box-shadow:var(--shadow);position:relative;display:flex;flex-direction:column}.product-photo{height:205px;background:var(--surface2);border-radius:15px;overflow:hidden;display:flex;align-items:center;justify-content:center}.product-photo img{width:100%;height:100%;object-fit:cover}.no-photo{font-size:60px}.heart{position:absolute;top:21px;right:21px;width:36px;height:36px;border-radius:50%;background:var(--surface);color:var(--text);padding:0;border:1px solid var(--line)}.heart.on{color:#bc303d}.product-info{padding:13px 4px 4px;display:flex;flex-direction:column;gap:7px;flex:1}.product-info h3{margin:0;font-size:16px;letter-spacing:-.3px}.muted{color:var(--muted)}.product-meta{font-size:12px;color:var(--muted)}.price-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:auto;padding-top:7px}.price{font-weight:850;font-size:19px;letter-spacing:-.4px}.mini-add{width:36px;height:36px;padding:0;border-radius:50%;font-size:20px}.stock{font-size:12px;color:var(--muted)}.panel{background:var(--surface);border:1px solid var(--line);border-radius:22px;padding:22px;margin:18px 0;box-shadow:var(--shadow)}.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 16px}.field{margin-bottom:13px}.field.full{grid-column:1/-1}.field label{display:block;font-size:13px;font-weight:700;margin-bottom:7px}.field input,.field select,.field textarea{width:100%;border:1px solid var(--line);border-radius:12px;background:var(--bg);color:var(--text);padding:12px 13px;outline-color:var(--green2)}.field textarea{min-height:90px;resize:vertical}.notice{background:var(--surface2);border:1px solid var(--line);padding:13px 16px;border-radius:13px;margin:13px 0}.table-wrap{overflow-x:auto}.table-product-image{width:68px;height:68px;object-fit:cover;border-radius:12px;background:var(--surface2);display:block}.table-product-placeholder{width:68px;height:68px;border-radius:12px;background:var(--surface2);display:grid;place-items:center;font-size:25px}table{width:100%;border-collapse:collapse;min-width:650px}th,td{text-align:left;padding:13px 11px;border-bottom:1px solid var(--line);font-size:14px}th{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.05em}.status{display:inline-block;border-radius:999px;padding:5px 9px;font-size:12px;background:var(--surface2)}.footer{margin-top:60px;padding:30px 0;border-top:1px solid var(--line);color:var(--muted);font-size:13px}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px}.empty{text-align:center;padding:50px 20px;color:var(--muted)}.empty .symbol{font-size:45px;margin-bottom:10px}.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:35px;align-items:center}.detail-photo{height:450px;border-radius:25px;background:var(--surface2);display:flex;align-items:center;justify-content:center;overflow:hidden}.detail-photo img{width:100%;height:100%;object-fit:contain}.detail-photo .no-photo{font-size:130px}.detail-title{font-size:clamp(32px,4vw,48px);letter-spacing:-1.8px;line-height:1.04;margin:10px 0}.qty{display:flex;align-items:center;gap:13px}.qty input{width:65px;text-align:center;border:1px solid var(--line);background:var(--surface);color:var(--text);padding:10px;border-radius:999px}.cart-item{display:flex;gap:14px;padding:14px 0;border-bottom:1px solid var(--line);align-items:center}.cart-item:last-of-type{border-bottom:0}.cart-item-photo{width:86px;height:86px;flex:0 0 86px;background:var(--surface2);border-radius:14px;display:grid;place-items:center;overflow:hidden}.cart-item-photo img{width:100%;height:100%;object-fit:cover}.cart-item-info{flex:1;min-width:0}.cart-item-name{display:block;margin-bottom:5px}.cart-item-subtotal{display:block;margin-top:7px}.cart-controls{display:flex;align-items:center;gap:8px;margin-top:9px}.cart-qty-btn{width:34px;height:34px;padding:0;border-radius:50%;background:var(--surface2);color:var(--text);border:1px solid var(--line);font-size:19px}.cart-qty-value{min-width:24px;text-align:center;font-weight:750}.cart-qty-btn:disabled{opacity:.35;cursor:not-allowed;transform:none}.cart-remove-form{margin-left:4px}.cart-remove-btn{width:38px;height:38px;padding:0;background:var(--surface2);color:var(--text);border:1px solid var(--line);font-size:20px}.cart-summary-total{font-size:20px}.mobile-bottom{display:none}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.metric{background:var(--surface2);padding:18px;border-radius:16px}.metric small{display:block;color:var(--muted);margin-bottom:8px}.metric strong{font-size:26px}.admin-side{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.small{font-size:12px}
@media(max-width:900px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}.navlinks{gap:12px}.search{min-width:150px}.hero{padding:35px}.hero h1{font-size:48px}.metric-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:650px){.wrap{width:92%}.nav{min-height:64px;flex-wrap:wrap;padding:10px 0}.navlinks{order:3;width:100%;overflow-x:auto;padding:2px 0 7px;gap:17px}.navlinks a{white-space:nowrap}.navactions .search{min-width:0;width:42px;padding:0;justify-content:center;border:0;background:transparent}.navactions .search input{display:none}.navactions .search span{font-size:19px}.hero{grid-template-columns:1fr;min-height:0;padding:30px 25px;margin-top:20px;border-radius:24px}.hero h1{font-size:43px;letter-spacing:-2px}.hero-art{min-height:150px}.hero-art img{height:180px}.hero-placeholder{font-size:100px}.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}.product-card{padding:8px;border-radius:17px}.product-photo{height:145px;border-radius:12px}.product-info{padding:10px 3px 4px}.product-info h3{font-size:14px}.price{font-size:16px}.heart{top:14px;right:14px;width:31px;height:31px}.section-head{align-items:start}.section-head h2{font-size:25px}.detail-grid,.two-col{grid-template-columns:1fr;gap:20px}.detail-photo{height:310px}.form-grid{grid-template-columns:1fr}.field.full{grid-column:auto}.panel{padding:16px;border-radius:18px}.mobile-bottom{display:flex;position:fixed;bottom:10px;left:4%;width:92%;z-index:12;background:var(--surface);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:20px;justify-content:space-around;padding:9px}.mobile-bottom a{display:flex;flex-direction:column;align-items:center;gap:3px;font-size:10px;color:var(--muted)}.mobile-bottom b{font-size:19px;color:var(--text)}.footer{padding-bottom:95px}.metric-grid{grid-template-columns:repeat(2,1fr)}body{padding-bottom:65px}}
"""

BASE = r'''<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ title }} · Shopmobi</title><style>''' + CSS + r'''</style></head><body>
<div class="topbar"><div class="wrap nav"><a class="logo" href="{{ url_for('home') }}">shop<span>mobi.</span></a>
<nav class="navlinks"><a href="{{ url_for('home') }}">Discover</a><a href="{{ url_for('home', category='Home & Living') }}">Home & Living</a><a href="{{ url_for('home', category='Fashion') }}">Fashion</a><a href="{{ url_for('merchant_register') }}">Sell with us</a></nav>
<div class="navactions"><form class="search" method="get" action="{{ url_for('home') }}"><span>⌕</span><input name="q" value="{{ request.args.get('q','') }}" placeholder="Search products"></form><a class="btn btn-light" href="{{ url_for('cart') }}" aria-label="Cart">♧ <span>{{ cart_count }}</span></a><button class="icon-btn" id="themeToggle" type="button" aria-label="Toggle night mode">☾</button></div></div></div>
<main class="wrap">{% with messages=get_flashed_messages() %}{% for message in messages %}<div class="notice">{{ message }}</div>{% endfor %}{% endwith %}{{ content|safe }}</main>
<div class="mobile-bottom"><a href="{{ url_for('home') }}"><b>⌂</b>Shop</a><a href="{{ url_for('favorites_page') }}"><b>♡</b>Saved</a><a href="{{ url_for('cart') }}"><b>♧</b>Cart</a><a href="{{ url_for('merchant_login') }}"><b>♙</b>Seller</a><a href="{{ url_for('admin_login') }}"><b>⚙</b>Admin</a></div>
<footer class="footer"><div class="wrap" style="display:flex;justify-content:space-between;gap:15px;flex-wrap:wrap"><span><strong>shopmobi.</strong> A little more style in every day.</span><span>Demo store · No real payments enabled</span></div></footer>
<script>
(function(){const root=document.documentElement;let saved='light';try{saved=localStorage.getItem('shopmobi-theme')||'light'}catch(e){}root.dataset.theme=saved;const btn=document.getElementById('themeToggle');function update(){if(btn)btn.textContent=root.dataset.theme==='dark'?'☀':'☾';}update();if(btn)btn.addEventListener('click',()=>{root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';try{localStorage.setItem('shopmobi-theme',root.dataset.theme)}catch(e){}update()});})();
</script></body></html>'''


def render_page(title, template, **context):
    cid = session.get("customer_id", "")
    cart_count = sum(carts.get(cid, {}).values())
    inner = render_template_string(template, **context)
    return render_template_string(BASE, title=title, content=inner, cart_count=cart_count)


def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_merchant():
    mid = session.get("merchant_id")
    return next((m for m in merchants if m["id"] == mid), None)


def seller_approved(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        merchant = current_merchant()
        if not merchant:
            flash("Please sign in to your seller account first.")
            return redirect(url_for("merchant_login"))
        if merchant["status"] != "approved":
            flash("Your seller account must be approved before you can manage products.")
            return redirect(url_for("merchant_login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


@app.before_request
def ensure_customer():
    if "customer_id" not in session:
        session["customer_id"] = uuid4().hex


@app.route("/")
def home():
    query = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "").strip()
    categories = sorted({p["category"] for p in products})
    visible = [p for p in products if p["stock"] > 0 and (not query or query in p["name"].lower() or query in p["description"].lower()) and (not category or p["category"] == category)]
    content = r'''
    <section class="hero"><div><small>✦ Thoughtfully picked finds</small><h1>Make space for something better.</h1><p>Discover pieces you’ll love, from everyday essentials to little upgrades that make life feel special.</p><a class="btn" href="#catalog">Explore the catalog ↗</a></div><div class="hero-art"><div class="hero-placeholder" aria-label="Shopping bag">🛍️</div></div></section>
    <div class="section-head"><div><h2 id="catalog">The catalog</h2><p>Find your next favourite thing.</p></div><span class="muted small">{{ visible|length }} products</span></div>
    <div class="chips"><a class="chip {% if not selected_category %}active{% endif %}" href="{{ url_for('home', q=query) }}">All items</a>{% for c in ['Electronics','Fashion','Beauty','Home & Living','Home','Food','Books','Sports','Other'] %}<a class="chip {% if selected_category==c %}active{% endif %}" href="{{ url_for('home', category=c, q=query) }}">{{ c }}</a>{% endfor %}</div>
    {% if visible %}<div class="grid">{% for p in visible %}<article class="product-card"><a href="{{ url_for('product_detail', product_id=p.id) }}"><div class="product-photo">{% if p.image %}<img src="{{ url_for('static', filename='uploads/'+p.image) }}" alt="{{ p.name }}">{% else %}<div class="no-photo">{% if p.category in ['Fashion'] %}👜{% elif p.category in ['Electronics'] %}🎧{% elif p.category in ['Beauty'] %}🧴{% elif p.category in ['Home','Home & Living'] %}🪑{% elif p.category=='Books' %}📚{% else %}✦{% endif %}</div>{% endif %}</div></a><form method="post" action="{{ url_for('toggle_favorite', product_id=p.id) }}"><button class="heart {% if p.id in favorite_ids %}on{% endif %}" title="Save to favourites">{% if p.id in favorite_ids %}♥{% else %}♡{% endif %}</button></form><div class="product-info"><div class="product-meta">{{ p.category }} · {{ p.seller_name }}</div><a href="{{ url_for('product_detail', product_id=p.id) }}"><h3>{{ p.name }}</h3></a><div class="price-row"><div><div class="price">KSh {{ '%.2f'|format(p.price) }}</div><div class="stock">{{ p.stock }} available</div></div><form method="post" action="{{ url_for('add_to_cart', product_id=p.id) }}"><input type="hidden" name="quantity" value="1"><button class="mini-add" aria-label="Add to cart">+</button></form></div></div></article>{% endfor %}</div>{% else %}<div class="panel empty"><div class="symbol">⌕</div><h3>No products found yet</h3><p>Try another search, or add products through an approved seller account.</p><a class="btn btn-light" href="{{ url_for('home') }}">Clear filters</a></div>{% endif %}
    '''
    favorite_ids = favorites.get(session["customer_id"], set())
    return render_page("Discover", content, visible=visible, categories=categories, query=query, selected_category=category, favorite_ids=favorite_ids)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    p = next((x for x in products if x["id"] == product_id), None)
    if not p:
        flash("Product not found.")
        return redirect(url_for("home"))
    content = r'''<div class="section-head"><a class="muted" href="{{ url_for('home') }}">← Back to catalog</a></div><section class="detail-grid"><div class="detail-photo">{% if p.image %}<img src="{{ url_for('static', filename='uploads/'+p.image) }}" alt="{{ p.name }}">{% else %}<div class="no-photo">✦</div>{% endif %}</div><div><div class="product-meta">{{ p.category }} · Sold by {{ p.seller_name }}</div><h1 class="detail-title">{{ p.name }}</h1><div class="price" style="font-size:28px;margin:18px 0">KSh {{ '%.2f'|format(p.price) }}</div><p class="muted" style="line-height:1.8">{{ p.description or 'A lovely find selected for your everyday life.' }}</p><p class="stock">{% if p.stock %}● In stock · {{ p.stock }} available{% else %}Out of stock{% endif %}</p><form method="post" action="{{ url_for('add_to_cart', product_id=p.id) }}" class="panel"><div class="field"><label>Quantity</label><div class="qty"><input type="number" name="quantity" value="1" min="1" max="{{ p.stock }}" required {% if not p.stock %}disabled{% endif %}><span class="muted small">Choose how many you need</span></div></div><button class="btn-green" style="width:100%" {% if not p.stock %}disabled{% endif %}>Add to cart ↗</button></form><form method="post" action="{{ url_for('toggle_favorite', product_id=p.id) }}"><button class="btn btn-light">♡ Save to favourites</button></form><p class="muted small">Demo checkout only. No real payments are collected.</p></div></section>'''
    return render_page(p["name"], content, p=p)


@app.route("/favorites")
def favorites_page():
    ids = favorites.get(session["customer_id"], set())
    saved = [p for p in products if p["id"] in ids]
    content = r'''<div class="section-head"><div><h2>Your favourites ♡</h2><p>Products you have saved.</p></div></div>{% if saved %}<div class="grid">{% for p in saved %}<article class="product-card"><a href="{{ url_for('product_detail', product_id=p.id) }}"><div class="product-photo">{% if p.image %}<img src="{{ url_for('static',filename='uploads/'+p.image) }}" alt="{{ p.name }}">{% else %}<div class="no-photo">✦</div>{% endif %}</div><div class="product-info"><h3>{{ p.name }}</h3><div class="price">KSh {{ '%.2f'|format(p.price) }}</div></div></a></article>{% endfor %}</div>{% else %}<div class="panel empty"><div class="symbol">♡</div><h3>No saved items yet</h3><p>Tap the heart on a product to save it here.</p><a class="btn" href="{{ url_for('home') }}">Explore products</a></div>{% endif %}'''
    return render_page("Favourites", content, saved=saved)


@app.route("/favorites/toggle/<int:product_id>", methods=["POST"])
def toggle_favorite(product_id):
    if not any(p["id"] == product_id for p in products):
        flash("Product not found.")
    else:
        saved = favorites.setdefault(session["customer_id"], set())
        if product_id in saved:
            saved.remove(product_id)
            flash("Removed from favourites.")
        else:
            saved.add(product_id)
            flash("Added to favourites.")
    return redirect(request.referrer or url_for("home"))


@app.route("/cart")
def cart():
    cid = session["customer_id"]
    rows, total = [], 0
    for pid, qty in carts.get(cid, {}).items():
        p = next((x for x in products if x["id"] == int(pid)), None)
        if p:
            subtotal = p["price"] * qty
            total += subtotal
            rows.append({"product": p, "quantity": qty, "subtotal": subtotal})
    content = r'''<div class="section-head"><div><h2>Your bag</h2><p>Good choices start here.</p></div></div>
    {% if rows %}
    <div class="two-col">
      <div class="panel">
        {% for row in rows %}
        <div class="cart-item">
          <div class="cart-item-photo">
            {% if row.product.image %}
              <img src="{{ url_for('static', filename='uploads/' + row.product.image) }}" alt="{{ row.product.name }}">
            {% else %}✦{% endif %}
          </div>
          <div class="cart-item-info">
            <strong class="cart-item-name">{{ row.product.name }}</strong>
            <span class="muted small">KSh {{ '%.2f'|format(row.product.price) }} each · {{ row.product.stock }} available</span>
            <div class="cart-controls" aria-label="Quantity controls for {{ row.product.name }}">
              <form method="post" action="{{ url_for('update_cart_quantity', product_id=row.product.id) }}">
                <input type="hidden" name="action" value="decrease">
                <button class="cart-qty-btn" type="submit" aria-label="Decrease quantity" {% if row.quantity <= 1 %}disabled{% endif %}>−</button>
              </form>
              <span class="cart-qty-value" aria-live="polite">{{ row.quantity }}</span>
              <form method="post" action="{{ url_for('update_cart_quantity', product_id=row.product.id) }}">
                <input type="hidden" name="action" value="increase">
                <button class="cart-qty-btn" type="submit" aria-label="Increase quantity" {% if row.quantity >= row.product.stock %}disabled{% endif %}>+</button>
              </form>
              <form class="cart-remove-form" method="post" action="{{ url_for('remove_cart_item', product_id=row.product.id) }}">
                <button class="cart-remove-btn" type="submit" title="Remove item" aria-label="Remove {{ row.product.name }} from cart">×</button>
              </form>
            </div>
            <strong class="cart-item-subtotal">KSh {{ '%.2f'|format(row.subtotal) }}</strong>
          </div>
        </div>
        {% endfor %}
        <p><a href="{{ url_for('home') }}" class="muted">← Continue shopping</a></p>
      </div>
      <div class="panel">
        <h3>Order summary</h3>
        <div style="display:flex;justify-content:space-between;margin:20px 0"><span class="muted">Subtotal</span><strong>KSh {{ '%.2f'|format(total) }}</strong></div>
        <div style="display:flex;justify-content:space-between;border-top:1px solid var(--line);padding-top:18px" class="cart-summary-total"><strong>Total</strong><strong>KSh {{ '%.2f'|format(total) }}</strong></div>
        <form method="post" action="{{ url_for('checkout') }}">
          <div class="field"><label>Full name</label><input name="name" required></div>
          <div class="field"><label>Phone number</label><input name="phone" required></div>
          <div class="field"><label>Delivery address</label><textarea name="address" required></textarea></div>
          <button class="btn-green" style="width:100%" type="submit">Place demo order</button>
        </form>
        <p class="muted small">No payment will be taken. This is a demonstration checkout.</p>
      </div>
    </div>
    {% else %}
    <div class="panel empty"><div class="symbol">♧</div><h3>Your bag is taking a little break</h3><p>Add something lovely from the catalog.</p><a class="btn" href="{{ url_for('home') }}">Explore catalog</a></div>
    {% endif %}'''
    return render_page("Your bag", content, rows=rows, total=total)


@app.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_cart_item(product_id):
    carts.get(session["customer_id"], {}).pop(str(product_id), None)
    flash("Item removed from your bag.")
    return redirect(url_for("cart"))


@app.route("/cart/update/<int:product_id>", methods=["POST"])
def update_cart_quantity(product_id):
    cid = session["customer_id"]
    bag = carts.get(cid, {})
    product_key = str(product_id)

    if product_key not in bag:
        flash("This product is not in your cart.")
        return redirect(url_for("cart"))

    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        bag.pop(product_key, None)
        flash("Product is no longer available and was removed from your cart.")
        return redirect(url_for("cart"))

    current_quantity = bag[product_key]
    action = request.form.get("action", "").strip().lower()

    if action == "increase":
        requested_quantity = current_quantity + 1
    elif action == "decrease":
        requested_quantity = current_quantity - 1
    else:
        try:
            requested_quantity = int(request.form.get("quantity", current_quantity))
        except (ValueError, TypeError):
            flash("Invalid quantity.")
            return redirect(url_for("cart"))

    if requested_quantity < 1:
        flash("Quantity cannot be less than 1.")
    elif requested_quantity > product["stock"]:
        flash(f"Only {product['stock']} items are available.")
    else:
        bag[product_key] = requested_quantity
        flash("Cart quantity updated successfully.")

    return redirect(url_for("cart"))


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    p = next((x for x in products if x["id"] == product_id), None)
    if not p or p["stock"] < 1:
        flash("This product is currently unavailable.")
        return redirect(request.referrer or url_for("home"))
    try:
        qty = int(request.form.get("quantity", 1))
    except ValueError:
        qty = 1
    bag = carts.setdefault(session["customer_id"], {})
    current = bag.get(str(product_id), 0)
    if qty < 1 or current + qty > p["stock"]:
        flash("Please select a valid quantity within the available stock.")
    else:
        bag[str(product_id)] = current + qty
        flash("Added to your bag.")
    return redirect(request.referrer or url_for("home"))


@app.route("/checkout", methods=["POST"])
def checkout():
    global next_order_id
    cid, bag = session["customer_id"], carts.get(session["customer_id"], {})
    if not bag:
        flash("Your bag is empty.")
        return redirect(url_for("cart"))
    name, phone, address = (request.form.get(k, "").strip() for k in ("name", "phone", "address"))
    if not name or not phone or not address:
        flash("Please complete all delivery details.")
        return redirect(url_for("cart"))
    items, total = [], 0
    for pid, qty in bag.items():
        p = next((x for x in products if x["id"] == int(pid)), None)
        if not p or qty > p["stock"]:
            flash("A product is unavailable or has insufficient stock. Please review your bag.")
            return redirect(url_for("cart"))
        subtotal = p["price"] * qty
        items.append({"product_id": p["id"], "name": p["name"], "merchant_id": p["merchant_id"], "quantity": qty, "price": p["price"], "subtotal": subtotal})
        total += subtotal
    for item in items:
        next(p for p in products if p["id"] == item["product_id"])["stock"] -= item["quantity"]
    orders.append({"id": next_order_id, "customer_name": name, "phone": phone, "address": address, "items": items, "total": total, "status": "New"})
    next_order_id += 1
    carts[cid] = {}
    flash("Demo order placed! No payment was collected.")
    return redirect(url_for("home"))


@app.route("/seller/register", methods=["GET", "POST"])
def merchant_register():
    global next_merchant_id
    if request.method == "POST":
        name, email, password = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower(), request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your seller name, email, and a password of at least 8 characters.")
        elif any(m["email"] == email for m in merchants):
            flash("That email already has an account.")
        else:
            merchants.append({"id": next_merchant_id, "name": name, "email": email, "password_hash": generate_password_hash(password), "status": "pending"})
            next_merchant_id += 1
            flash("Seller application submitted. Please wait for admin approval.")
            return redirect(url_for("merchant_login"))
    content = r'''<div class="section-head"><div><h2>Become a seller</h2><p>Bring your products to the Shopmobi community.</p></div></div><div class="panel"><form method="post"><div class="field"><label>Business or seller name</label><input name="name" required></div><div class="field"><label>Email address</label><input type="email" name="email" required></div><div class="field"><label>Password (minimum 8 characters)</label><input type="password" name="password" minlength="8" required></div><button class="btn-green">Submit application ↗</button></form></div>'''
    return render_page("Seller application", content)


@app.route("/seller/login", methods=["GET", "POST"])
def merchant_login():
    if request.method == "POST":
        email, password = request.form.get("email", "").strip().lower(), request.form.get("password", "")
        m = next((x for x in merchants if x["email"] == email), None)
        if m and check_password_hash(m["password_hash"], password):
            if m["status"] != "approved":
                flash("Your seller account is " + m["status"] + ". Please wait for admin approval.")
            else:
                session["merchant_id"] = m["id"]
                return redirect(url_for("merchant_dashboard"))
        else:
            flash("Incorrect email or password.")
    content = r'''<div class="section-head"><div><h2>Seller sign in</h2><p>Manage your products and orders.</p></div></div><div class="panel"><form method="post"><div class="field"><label>Email address</label><input type="email" name="email" required></div><div class="field"><label>Password</label><input type="password" name="password" required></div><button class="btn-green">Sign in</button></form><p class="muted">New to Shopmobi? <a href="{{ url_for('merchant_register') }}"><strong>Apply to sell</strong></a></p></div>'''
    return render_page("Seller sign in", content)


@app.route("/seller/logout")
def merchant_logout():
    session.pop("merchant_id", None)
    flash("You have signed out.")
    return redirect(url_for("home"))


@app.route("/seller/dashboard")
@seller_approved
def merchant_dashboard():
    m = current_merchant()
    own_products = [p for p in products if p["merchant_id"] == m["id"]]
    own_orders = [{"order": o, "items": [i for i in o["items"] if i["merchant_id"] == m["id"]]} for o in orders if any(i["merchant_id"] == m["id"] for i in o["items"])]
    sales = sum(i["subtotal"] for e in own_orders for i in e["items"])
    content = r'''<div class="section-head"><div><h2>Seller studio</h2><p>Welcome back, {{ m.name }}.</p></div><a class="btn btn-green" href="{{ url_for('product_add') }}">＋ Add product</a></div><div class="metric-grid"><div class="metric"><small>Your products</small><strong>{{ own_products|length }}</strong></div><div class="metric"><small>Orders with your items</small><strong>{{ own_orders|length }}</strong></div><div class="metric"><small>Units in stock</small><strong>{{ own_products|sum(attribute='stock') }}</strong></div><div class="metric"><small>Demo sales total</small><strong style="font-size:20px">KSh {{ '%.0f'|format(sales) }}</strong></div></div><div class="section-head"><div><h2>Your products</h2><p>Keep listings and stock up to date.</p></div></div>{% if own_products %}<div class="panel table-wrap"><table><tr><th>Photo</th><th>Product</th><th>Price</th><th>Stock</th><th>Actions</th></tr>{% for p in own_products %}<tr><td>{% if p.image %}<img class="table-product-image" src="{{ url_for('static', filename='uploads/'+p.image) }}" alt="{{ p.name }}">{% else %}<div class="table-product-placeholder">✦</div>{% endif %}</td><td>{{ p.name }}</td><td>KSh {{ '%.2f'|format(p.price) }}</td><td>{{ p.stock }}</td><td><a class="btn btn-light" href="{{ url_for('product_edit', product_id=p.id) }}">Edit</a> <form style="display:inline" method="post" action="{{ url_for('product_delete', product_id=p.id) }}"><button class="btn-danger">Delete</button></form></td></tr>{% endfor %}</table></div>{% else %}<div class="panel empty">No products yet. Add your first listing to get started.</div>{% endif %}<div class="section-head"><div><h2>Recent orders</h2><p>Orders that contain your products.</p></div></div>{% for entry in own_orders %}<div class="panel"><strong>Order #{{ entry.order.id }}</strong><span class="status">{{ entry.order.status }}</span><p class="muted">{{ entry.order.customer_name }} · {{ entry.order.phone }}</p>{% for i in entry.items %}<p>{{ i.name }} × {{ i.quantity }} — KSh {{ '%.2f'|format(i.subtotal) }}</p>{% endfor %}</div>{% else %}<div class="panel">No orders yet.</div>{% endfor %}<p><a class="btn btn-light" href="{{ url_for('merchant_logout') }}">Sign out</a></p>'''
    return render_page("Seller studio", content, m=m, own_products=own_products, own_orders=own_orders, sales=sales)


@app.route("/seller/products/add", methods=["GET", "POST"])
@seller_approved
def product_add():
    global next_product_id
    if request.method == "POST":
        name, description, category = request.form.get("name", "").strip(), request.form.get("description", "").strip(), request.form.get("category", "Other").strip()
        try:
            price, stock = float(request.form.get("price", "0")), int(request.form.get("stock", "0"))
        except ValueError:
            price, stock = -1, -1
        image = request.files.get("image")
        if not name or price <= 0 or stock < 0:
            flash("Enter a product name, positive price, and valid stock quantity.")
        elif not image or not image.filename:
            flash("Please choose a product photo from your computer before saving.")
        elif not allowed_image(image.filename):
            flash("Use a JPG, JPEG, PNG, or WEBP image.")
        else:
            try:
                filename = secure_filename(f"{next_product_id}_{uuid4().hex[:8]}_{image.filename}")
                image.save(UPLOAD_FOLDER / filename)
                if not (UPLOAD_FOLDER / filename).is_file():
                    raise OSError("The uploaded image was not saved successfully.")
            except OSError:
                flash("The image could not be saved. Check that static/uploads is writable.")
            else:
                m = current_merchant()
                products.append({"id": next_product_id, "merchant_id": m["id"], "seller_name": m["name"], "name": name, "description": description, "category": category, "price": price, "stock": stock, "image": filename})
                next_product_id += 1
                flash("Product and photo added successfully.")
                return redirect(url_for("merchant_dashboard"))
    content = r'''<div class="section-head"><div><h2>Add a product</h2><p>Create a clean listing for your customers.</p></div></div><div class="panel"><form method="post" enctype="multipart/form-data"><div class="form-grid"><div class="field"><label>Product name</label><input name="name" required></div><div class="field"><label>Category</label><select name="category">{% for c in ['Electronics','Fashion','Beauty','Home & Living','Home','Food','Books','Sports','Other'] %}<option>{{ c }}</option>{% endfor %}</select></div><div class="field"><label>Price (KSh)</label><input type="number" name="price" min="0.01" step="0.01" required></div><div class="field"><label>Stock quantity</label><input type="number" name="stock" min="0" step="1" required></div><div class="field full"><label>Description</label><textarea name="description" placeholder="Describe the product..."></textarea></div><div class="field full"><label>Product photo (JPG, PNG, WEBP; max 5 MB)</label><input type="file" name="image" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" required></div></div><button class="btn-green" type="submit">Save product</button> <a class="btn btn-light" href="{{ url_for('merchant_dashboard') }}">Cancel</a></form></div>'''
    return render_page("Add product", content)


@app.route("/seller/products/<int:product_id>/edit", methods=["GET", "POST"])
@seller_approved
def product_edit(product_id):
    p = next((x for x in products if x["id"] == product_id), None)
    m = current_merchant()
    if not p or p["merchant_id"] != m["id"]:
        flash("Product not found.")
        return redirect(url_for("merchant_dashboard"))
    if request.method == "POST":
        try:
            price, stock = float(request.form.get("price", "0")), int(request.form.get("stock", "0"))
        except ValueError:
            price, stock = -1, -1
        image = request.files.get("image")
        if price <= 0 or stock < 0:
            flash("Enter a positive price and valid stock quantity.")
        elif image and image.filename and not allowed_image(image.filename):
            flash("Use a JPG, JPEG, PNG, or WEBP image.")
        else:
            p.update(name=request.form.get("name", "").strip(), description=request.form.get("description", "").strip(), category=request.form.get("category", "Other").strip(), price=price, stock=stock)
            if image and image.filename:
                filename = secure_filename(f"{product_id}_{uuid4().hex[:8]}_{image.filename}")
                image.save(UPLOAD_FOLDER / filename)
                p["image"] = filename
            flash("Product updated.")
            return redirect(url_for("merchant_dashboard"))
    content = r'''<div class="section-head"><div><h2>Edit product</h2><p>Update your listing.</p></div></div><div class="panel"><form method="post" enctype="multipart/form-data"><div class="field"><label>Product name</label><input name="name" value="{{ p.name }}" required></div><div class="field"><label>Category</label><select name="category">{% for c in ['Electronics','Fashion','Beauty','Home & Living','Home','Food','Books','Sports','Other'] %}<option {% if p.category==c %}selected{% endif %}>{{ c }}</option>{% endfor %}</select></div><div class="field"><label>Description</label><textarea name="description">{{ p.description }}</textarea></div><div class="form-grid"><div class="field"><label>Price (KSh)</label><input type="number" name="price" min="0.01" step="0.01" value="{{ p.price }}" required></div><div class="field"><label>Stock</label><input type="number" name="stock" min="0" value="{{ p.stock }}" required></div></div>{% if p.image %}<div class="field"><label>Current product photo</label><img class="table-product-image" style="width:150px;height:150px" src="{{ url_for('static', filename='uploads/' + p.image) }}" alt="{{ p.name }} photo"></div>{% endif %}<div class="field"><label>Replace photo (optional)</label><input type="file" name="image" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"></div><button class="btn-green">Save changes</button> <a class="btn btn-light" href="{{ url_for('merchant_dashboard') }}">Cancel</a></form></div>'''
    return render_page("Edit product", content, p=p)


@app.route("/seller/products/<int:product_id>/delete", methods=["POST"])
@seller_approved
def product_delete(product_id):
    p = next((x for x in products if x["id"] == product_id), None)
    if p and p["merchant_id"] == current_merchant()["id"]:
        products.remove(p)
        for saved in favorites.values():
            saved.discard(product_id)
        for bag in carts.values():
            bag.pop(str(product_id), None)
        flash("Product deleted.")
    else:
        flash("Product not found.")
    return redirect(url_for("merchant_dashboard"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("username", "") == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, request.form.get("password", "")):
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect admin username or password.")
    content = r'''<div class="section-head"><div><h2>Admin sign in</h2><p>Manage the Shopmobi marketplace.</p></div></div><div class="panel"><form method="post"><div class="field"><label>Username</label><input name="username" required></div><div class="field"><label>Password</label><input type="password" name="password" required></div><button class="btn-green">Sign in</button></form><p class="muted small">Demo credentials: admin / ChangeMe123!</p></div>'''
    return render_page("Admin sign in", content)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("home"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    pending = sum(m["status"] == "pending" for m in merchants)
    content = r'''<div class="section-head"><div><h2>Marketplace overview</h2><p>Review seller applications and keep an eye on the store.</p></div><a class="btn btn-light" href="{{ url_for('admin_logout') }}">Sign out</a></div><div class="metric-grid"><div class="metric"><small>Total sellers</small><strong>{{ merchants|length }}</strong></div><div class="metric"><small>Pending approvals</small><strong>{{ pending }}</strong></div><div class="metric"><small>Total products</small><strong>{{ products|length }}</strong></div><div class="metric"><small>Demo orders</small><strong>{{ orders|length }}</strong></div></div><div class="section-head"><div><h2>Seller applications</h2><p>Approve sellers before they can list products.</p></div></div>{% for m in merchants %}<div class="panel" style="display:flex;align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap"><div><strong>{{ m.name }}</strong><p class="muted small">{{ m.email }}</p><span class="status">{{ m.status }}</span></div><div class="admin-side">{% if m.status!='approved' %}<form method="post" action="{{ url_for('merchant_decision', merchant_id=m.id, decision='approve') }}"><button class="btn-green">Approve</button></form>{% endif %}{% if m.status!='rejected' %}<form method="post" action="{{ url_for('merchant_decision', merchant_id=m.id, decision='reject') }}"><button class="btn-danger">Reject</button></form>{% endif %}{% if m.status!='suspended' %}<form method="post" action="{{ url_for('merchant_decision', merchant_id=m.id, decision='suspend') }}"><button class="btn-light">Suspend</button></form>{% endif %}</div></div>{% else %}<div class="panel empty">No seller applications yet.</div>{% endfor %}<div class="section-head"><div><h2>All products</h2><p>Marketplace inventory overview.</p></div></div>{% if products %}<div class="panel table-wrap"><table><tr><th>Photo</th><th>Product</th><th>Seller</th><th>Category</th><th>Price</th><th>Stock</th></tr>{% for p in products %}<tr><td>{% if p.image %}<img class="table-product-image" src="{{ url_for('static', filename='uploads/'+p.image) }}" alt="{{ p.name }}">{% else %}<div class="table-product-placeholder">✦</div>{% endif %}</td><td>{{ p.name }}</td><td>{{ p.seller_name }}</td><td>{{ p.category }}</td><td>KSh {{ '%.2f'|format(p.price) }}</td><td>{{ p.stock }}</td></tr>{% endfor %}</table></div>{% else %}<div class="panel">No products have been listed yet.</div>{% endif %}<div class="section-head"><div><h2>Recent demo orders</h2></div></div>{% for o in orders %}<div class="panel"><strong>Order #{{ o.id }}</strong> <span class="status">{{ o.status }}</span><p class="muted">{{ o.customer_name }} · {{ o.phone }} · KSh {{ '%.2f'|format(o.total) }}</p></div>{% else %}<div class="panel">No orders yet.</div>{% endfor %}'''
    return render_page("Admin dashboard", content, merchants=merchants, products=products, orders=orders, pending=pending)


@app.route("/admin/merchants/<int:merchant_id>/<decision>", methods=["POST"])
@admin_required
def merchant_decision(merchant_id, decision):
    m = next((x for x in merchants if x["id"] == merchant_id), None)
    if not m or decision not in {"approve", "reject", "suspend"}:
        flash("Invalid seller or action.")
    else:
        m["status"] = {"approve": "approved", "reject": "rejected", "suspend": "suspended"}[decision]
        flash(f"Seller account {m['status']}.")
    return redirect(url_for("admin_dashboard"))


@app.errorhandler(413)
def file_too_large(error):
    return "Image is too large. Please upload an image smaller than 5 MB.", 413


if __name__ == "__main__":
    app.run(debug=True)
