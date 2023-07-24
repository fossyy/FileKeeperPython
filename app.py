import os
import asyncio
import hashlib
import aiosqlite
import json
import uuid
from quart import Quart, request, send_file, redirect, url_for, render_template, session, jsonify, make_response
from pathlib import Path
from werkzeug.utils import secure_filename

app = Quart(__name__)
app.secret_key = os.urandom(24) 
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  
# 20 x 1024 x 1024 adalah 20mb ini adalah max file yang bisa di upload ke backend

async def initialize_database():
    conn = await aiosqlite.connect('main.db')
    c = await conn.cursor()
    await c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT , password_hash TEXT, userid TEXT PRIMARY KEY)')
    await c.execute('CREATE TABLE IF NOT EXISTS uploaded_files (userid STRING, username TEXT, foldername TEXT, files TEXT)')
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
        userid = str(uuid.uuid4())
        await c.execute("INSERT INTO users (username, password_hash, userid) VALUES (?, ?, ?)", (username, password_hash, userid))
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

@app.route("/download/")
async def download_page():
    if not is_login():
        return redirect(url_for('index'))
    
    username = session.get('username')
    conn = await aiosqlite.connect('main.db')
    c = await conn.cursor()
    cursor = await c.execute("SELECT files FROM uploaded_files WHERE username = ?", (username,))
    filenames_json = await cursor.fetchone()
    await conn.close()

    if not filenames_json:
        return "No uploaded files found."
    userid = session.get('userid')
    files = json.loads(filenames_json[0])
    return await render_template('download.html', files=files, userid=userid)

@app.route("/download/file/<string:userid>/<string:fileid>")
async def download_file_path(userid, fileid):
    conn = await aiosqlite.connect('main.db')
    c = await conn.cursor()
    cursor = await c.execute("SELECT files FROM uploaded_files WHERE userid = ?", (userid,))
    data = await cursor.fetchone()
    files_data = json.loads(data[0])
    for file in files_data:
        if file['id'] == fileid:
            filename = file['name']
    file_path = Path(f"app/{userid}/{filename}")
    if file_path.is_file():
        return await send_file(file_path, as_attachment=True)
    else:
        return await make_response(jsonify({"message": "404: Not found"}), 404)
    
@app.route("/download/file/")
async def download_file():
    return await make_response(jsonify({"message": "401: Unauthorized"}), 401)

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
        return jsonify({"message": "400: No selected file."})

    filename = secure_filename(file.filename)
    fileid = str(uuid.uuid4())
    username = session.get('username')
    userid = session.get('userid')

    user_folder = get_user_folder(userid)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    file_path = os.path.join(user_folder, filename)
    await file.save(file_path)

    conn = await aiosqlite.connect('main.db')
    c = await conn.cursor()
    cursor = await c.execute("SELECT files FROM uploaded_files WHERE userid = ?", (userid,))
    files_json = await cursor.fetchone()

    if not files_json:
        files = [{
            "name": filename,
            "id": fileid
        }]
        await c.execute("INSERT INTO uploaded_files (userid, username, foldername, files) VALUES (?, ?, ?, ?)", (userid, username, user_folder, json.dumps(list(files))))
    else:
        # Deserialize the JSON data retrieved from the database
        files_data = json.loads(files_json[0])
        dataDict = []
        for file_entry in files_data:  # Use the variable `file_entry` to represent the dictionary in `files_data`
            dataDict.append({
                "name": file_entry["name"],
                "id": file_entry["id"]
            })
        dataDict.append({
            "name": filename,
            "id": fileid
        })
        await c.execute("UPDATE uploaded_files SET files = ? WHERE userid = ?", (json.dumps(list(dataDict)), userid))

    await conn.commit()
    await conn.close()

    return jsonify({"message": "200: Success"})

if __name__ == "__main__":
    asyncio.run(initialize_database())
    app.run()
