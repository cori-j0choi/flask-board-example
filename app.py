from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # 플래시 메시지를 위한 시크릿 키
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB 제한
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class BoardPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.Column(db.String(80), nullable=False)

class PhotoPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.Column(db.String(80), nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html', user=session.get('user'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('이미 존재하는 사용자 이름입니다.')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('회원가입이 완료되었습니다!')
        return redirect(url_for('home'))
    return render_template('register.html', user=session.get('user'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            flash('로그인 성공!')
            return redirect(url_for('home'))
        else:
            flash('아이디 또는 비밀번호가 올바르지 않습니다.')
            return redirect(url_for('login'))
    return render_template('login.html', user=session.get('user'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('로그아웃 되었습니다.')
    return redirect(url_for('home'))

@app.route('/user_list')
def user_list():
    if session.get('user') != 'admin':
        flash('관리자만 접근할 수 있습니다.')
        return redirect(url_for('home'))
    users = User.query.all()
    return render_template('user_list.html', users=users, user=session.get('user'))

@app.route('/board', methods=['GET', 'POST'])
def board():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        if not title or not content or not author:
            flash('모든 필드를 입력해주세요.')
            return redirect(url_for('board'))
        post = BoardPost(title=title, content=content, author=author)
        db.session.add(post)
        db.session.commit()
        flash('게시글이 등록되었습니다!')
        return redirect(url_for('board'))
    posts = BoardPost.query.order_by(BoardPost.created_at.desc()).all()
    return render_template('board.html', posts=posts, user=session.get('user'))

@app.route('/photo_board', methods=['GET', 'POST'])
def photo_board():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        file = request.files.get('photo')
        if not title or not author or not file:
            flash('모든 필드를 입력해주세요.')
            return redirect(url_for('photo_board'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(save_path):
                filename = f"{base}_{counter}{ext}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                counter += 1
            file.save(save_path)
            post = PhotoPost(title=title, filename=filename, author=author)
            db.session.add(post)
            db.session.commit()
            flash('사진이 업로드되었습니다!')
            return redirect(url_for('photo_board'))
        else:
            flash('허용되지 않는 파일 형식입니다.')
            return redirect(url_for('photo_board'))
    posts = PhotoPost.query.order_by(PhotoPost.created_at.desc()).all()
    return render_template('photo_board.html', posts=posts, user=session.get('user'))

if __name__ == '__main__':
    app.run(debug=True) 