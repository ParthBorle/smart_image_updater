from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import requests
from PIL import Image
from image_processor import process_image
PEXELS_API_KEY = "N8TTAhuqAcAavf4MmTMpmBAetQwso9suuXcMq40iF4kMW8AhX2Ytrwrf"
app = Flask(__name__)

app.secret_key = 'supersecretkey'
DB_PATH = 'database.db'
UPLOAD_FOLDER = 'static/images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- Database Functions ----------
def get_all_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, code, image_path FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

def insert_product(name, code, image_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, code, image_path) VALUES (?, ?, ?)", (name, code, image_path))
    conn.commit()
    conn.close()

def update_product_image(product_id, image_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET image_path = ? WHERE id = ?", (image_path, product_id))
    conn.commit()
    conn.close()

# ---------- Routes ----------
@app.route('/')
def index():
    products = get_all_products()
    return render_template('index.html', products=products)

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        session['name'] = name
        session['code'] = code
        return redirect(url_for('show_images', query=name))
    return render_template('add_product.html')


@app.route('/show_images')
def show_images():
    query = session.get('name', '')
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 10}
    resp = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)

    images = []
    if resp.status_code == 200:
        data = resp.json()
        images = [photo["src"]["medium"] for photo in data["photos"]]

    return render_template('image_selector.html', images=images)
@app.route('/select_image', methods=['POST'])
def select_image():
    selected_url = request.form['selected_image']
    name = session.get('name')
    code = session.get('code')

    if not selected_url or not name or not code:
        return "Invalid selection. Try again."

    response = requests.get(selected_url)
    if response.status_code == 200:
        image_filename = f"{code}.jpg"
        image_path = os.path.join(UPLOAD_FOLDER, image_filename)
        with open(image_path, 'wb') as f:
            f.write(response.content)

        process_image(image_path)  # ✅ Resize to 500x500
        insert_product(name, code, image_path)

    return redirect(url_for('index'))



@app.route('/upload/<int:product_id>', methods=['POST'])
def upload_image(product_id):
    file = request.files['image']
    if file:
        filename = f"{product_id}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        process_image(filepath)  # ✅ Resize to 500x500
        update_product_image(product_id, filepath)
    return redirect(url_for('index'))

@app.route('/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    # Delete the image file from disk
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT image_path FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if row and row[0] and os.path.exists(row[0]):
        os.remove(row[0])

    # Delete from database
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))




if __name__ == '__main__':
    app.run(debug=True)
