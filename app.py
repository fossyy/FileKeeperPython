import os
import asyncio
import hashlib
import aiosqlite
import json
from quart import Quart, request, send_file, redirect, url_for, render_template, session, jsonify
from pathlib import Path
from werkzeug.utils import secure_filename

app = Quart(__name__)
app.secret_key = os.urandom(24) 
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  
# 20 x 1024 x 1024 adalah 20mb ini adalah max file yang bisa di upload ke backend

async def initialize_database():
    conn = await aiosqlite.connect('main.db')
    c = await conn.cursor()
    await c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT , password_hash TEXT, userid INTEGER PRIMARY KEY AUTOINCREMENT)')
    await c.execute('CREATE TABLE IF NOT EXISTS uploaded_files (userid INTEGER, username TEXT, foldername TEXT, filenames TEXT)')
    await conn.commit()
    await conn.close()

def is_login():
    username = session.get('username')
    if username:
        return True
    else:
        return False
    
def get_user_folder(userid):
    return f"app/{userid}"

@app.route('/')
async def index():
    username = session.get('username')
    if username:
        return await render_template('index.html', username=username)
    else:
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
async def register():
    if is_login():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        form = await request.form
        username = form["username"]
        password = form["password"]

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = await aiosqlite.connect('main.db')
        c = await conn.cursor()
        cursor = await c.execute("SELECT * FROM users WHERE username = ?", (username,))

        user = await cursor.fetchone()
        if user:
            return "Username sudah dipakai"
        
        await c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        userid = c.lastrowid
        await conn.commit()
        await conn.close()

        return f"Registration successful, Your userid is {userid}"

    return await render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
async def login():
    if is_login():
        return redirect(url_for('index'))
    if request.method == 'POST':
        form = await request.form
        username = form["username"]
        password = form["password"]
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = await aiosqlite.connect('main.db')
        c = await conn.cursor()
        cursor = await c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = await cursor.fetchone()
        await conn.close()

        if user and user[1] == password_hash:
            session['username'] = user[0]
            session['userid'] = user[2]
            return redirect(url_for('index'))
        else:
            return "Invalid username or password"
    
    return await render_template('login.html')

@app.route("/logout")
async def logout():
    session.pop('username', None)
    session.pop('userid', None)
    return redirect(url_for('login'))

@app.route("/download")
async def download_page():
    if not is_login():
        return redirect(url_for('index'))
    
    username = session.get('username')
    conn = await aiosqlite.connect('main.db')
    c = await conn.cursor()
    cursor = await c.execute("SELECT filenames FROM uploaded_files WHERE username = ?", (username,))
    filenames_json = await cursor.fetchone()
    await conn.close()

    if not filenames_json:
        return "No uploaded files found."

    filenames = json.loads(filenames_json[0])
    return await render_template('download.html', files=filenames)

@app.route("/download/file/<string:filename>")
async def download_file(filename):
    if not is_login():
        return redirect(url_for('login'))
    
    userid = session.get('userid')
    file_path = Path(f"app/{userid}/{filename}")
    if file_path.is_file():
        return await send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404

@app.route('/upload', methods=['GET'])
async def upload():
    if not is_login():
        return redirect(url_for('login'))
    
    return await render_template('upload.html')

@app.route('/upload', methods=['POST'])
async def upload_file():
    if not is_login():
        return redirect(url_for('login'))
    data = await request.files
    file = data['file']
    if file.filename == '':
        return jsonify({"error": "No selected file."})

    filename = secure_filename(file.filename)
    username = session.get('username')
    userid = session.get('userid')

    user_folder = get_user_folder(userid)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    file_path = os.path.join(user_folder, filename)
    await file.save(file_path)

    conn = await aiosqlite.connect('main.db')
    c = await conn.cursor()
    cursor = await c.execute("SELECT filenames FROM uploaded_files WHERE userid = ?", (userid,))
    filenames_json = await cursor.fetchone()

    if not filenames_json:
        filenames = {filename}
        await c.execute("INSERT INTO uploaded_files (userid, username, foldername, filenames) VALUES (?, ?, ?, ?)", (userid, username, user_folder, json.dumps(list(filenames))))
    else:
        filenames = json.loads(filenames_json[0])
        filenames.append(filename)
        await c.execute("UPDATE uploaded_files SET filenames = ? WHERE userid = ?", (json.dumps(list(filenames)), userid))

    await conn.commit()
    await conn.close()

    return jsonify({"success": True})

if __name__ == "__main__":
    asyncio.run(initialize_database())
    app.run()
