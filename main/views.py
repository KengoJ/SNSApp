from flask import request,redirect,url_for,render_template,flash
from flask_login.utils import login_required
from main import app, db
from main.models import Chat, Entry, Thread, User, UserRelationship
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased 



#ログインマネージャのインスタンス作成
login_manager = LoginManager()
#flaskアプリとの紐付け
login_manager.init_app(app)
#ユーザーの認証
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#画像の保存先、許可する拡張子
UPLOAD_FOLDER = 'main/static/imgs/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#画像の形式を確認
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#トップページの表示
@app.route('/', methods=['GET'])
def top():
    return render_template('top.html',page_title="トップ")


#index の表示
@app.route('/index')
def bbs():
    #スレッドをすべて読み込んでindex.htmlに渡す
    threads = Thread.query.all()
    return render_template('bbs.html',threads=threads, page_title="BBS")


#スレッドの処理#ログイン要ページ
@app.route('/thread', methods=['POST','GET'])
@login_required
def thread():
    #index.htmlからthreadを取得
    thread_get = request.form['thread']
    
    #ThreadDBをすべて読み込み
    threads = Thread.query.all()
    #表示するスレッドのリスト
    thread_list = []
    #リストにスレッドのタイトルを追加
    for th in threads:
        thread_list.append(th.threadname)
    #すでに作成されているスレッドを開く処理
    if thread_get in thread_list:
        thread = Thread.query.filter_by(threadname=thread_get).first()
        articles = Entry.query.filter_by(thread_id=thread.id).all()
        return render_template('thread.html', articles=articles,thread=thread_get,page_title="スレッド")
    #新たにスレッドを作成した場合の処理
    else:
        thread_new = Thread(thread_get)
        db.session.add(thread_new)
        db.session.commit()
        articles = Entry.query.filter_by(thread_id=thread_new.id).all()
        return render_template('thread.html',articles=articles,thread=thread_get)
        

#投稿の処理
@app.route('/add',methods=['POST'])
@login_required
def add_entry():
    date = datetime.now()
    article = request.form['article']
    name = request.form['name']
    thread = request.form['thread']
    send_user_id = request.form['send_user_id']
    thread = Thread.query.filter_by(threadname=thread).first()
    admin = Entry(date=date, name=name, article=article, thread_id=thread.id, send_user_id=send_user_id)
    db.session.add(admin)
    db.session.commit()
    return render_template('result.html', article=article, thread=thread)


#新規登録の処理
@app.route('/signup',methods=['GET','POST'])
def signup():
    if  request.method == 'POST':
        username = request.form.get('username')
        login_user_id = request.form.get('login_user_id')
        password = request.form.get('password')

        #すでにユーザー名が使われている場合
        existed_check = User.query.filter_by(login_user_id=login_user_id).first()
        if existed_check:
            flash('登録済みのユーザーです')
            return render_template('signup.html')
        #UserDBへの追加
        user = User(username=username, login_user_id=login_user_id,
                     password=generate_password_hash(password, method='sha256'))
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else :
        return render_template('signup.html')


#ログインの処理
@app.route('/login',methods=['GET','POST'])
def login():
        if request.method == 'POST':
            login_user_id = request.form.get('login_user_id')
            password = request.form.get('password')
            #Userを検索しパスワードを照合する
            user = User.query.filter_by(login_user_id=login_user_id).first()
            if user is None:
                flash('ユーザーが存在しません')
            elif check_password_hash(user.password, password):
                login_user(user)
                return redirect('/index')
            else:
                flash('パスワードが違います')
            return render_template('/login.html')
        else:
                return render_template('/login.html')


#ログアウトの処理
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


#ログイン必須ページで認証が確認できなかった場合の処理
@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login')


#パスワード変更処理
@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        login_user_id = request.form.get('login_user_id')
        user = User.query.filter_by(login_user_id=login_user_id).first()
        if user is not None:
            new_password = request.form.get('new_password')
            with db.session.begin(subtransactions=True):
                user.password = generate_password_hash(new_password, method='sha256')
            db.session.commit()
            return redirect('/login')
        else:
            flash('ユーザーが存在しません')
            return render_template('/forgot_password.html')
    else:
         return render_template('/forgot_password.html')


#ユーザー情報の編集
@app.route('/setting', methods=['GET','POST'])
@login_required
def setting():
    user = User.query.filter_by(login_user_id=current_user.login_user_id).first()
    if request.method =='POST':
        name = request.form.get('user_name')
        login_user_id = request.form.get('login_user_id')
        with db.session.begin(subtransactions=True):
            if user is not None:
                user.username = name
                user.login_user_id = login_user_id
                file = request.files.get('file')
                if file and allowed_file(file.filename):
                    # ファイルの拡張子を取得する
                    _, ext = os.path.splitext(file.filename)
                    #ファイル名を設定# 小文字にして
                    file_name = current_user.login_user_id + ext.lower()
                    # ファイルを保存するディレクトリを指定
                    filepath = UPLOAD_FOLDER + file_name
                    # ファイルを保存する
                    file.save(filepath)
                    user.picture_path="imgs/" + file_name
                    
        db.session.commit()
        flash('更新しました')
        return render_template('/setting.html')
      
    else:
        return render_template('/setting.html')


#ユーザー検索
@app.route('/user_search', methods=['GET','POST'])
@login_required
def user_search():
        users = None
        #UserRelationshipのエイリアスを定義
        follow = aliased(UserRelationship)
        follower = aliased(UserRelationship)
        if request.method == 'POST':
            username = request.form.get('username')
            #usernameの部分一位検索
            #フォロー状態の双方向のテーブルを外部結合
            #フォロー状態の方向をlabelで設定
            users = User.query.filter(User.username.like(f'%{username}%'))\
            .outerjoin(follow,and_(follow.from_user_id == current_user.id,
            follow.to_user_id == User.id,))\
            .outerjoin(follower,and_(follower.from_user_id == User.id,
            follower.to_user_id == current_user.id,))\
            .with_entities(User.id, User.username, User.picture_path,
                follow.state.label('state_from_currentuser'),
                follower.state.label('state_from_opponentuser'))\
            .all()
            if users:   
                return render_template('user_search.html',users=users)
            
            flash('ユーザーが存在しません')
        return render_template('user_search.html',users = users)


#友達申請の処理
@app.route('/follow', methods=['POST'])
@login_required
def follow():
    from_user_id = current_user.id
    to_user_id = request.form.get('to_user_id')
    connect = UserRelationship(from_user_id, to_user_id,state=1)
    with db.session.begin(subtransactions=True):
        db.session.add(connect)
    db.session.commit()
    flash('フォローリクエストを送りました')
    return render_template('user_search.html')


#フォロー解除の処理
@app.route('/follow_lift', methods=['POST'])
@login_required
def follow_lift():
    opponent_id = request.form.get('opponent_id')
    #ログインしているユーザーからのフォローを取得
    lift = UserRelationship.query.filter(
            and_(
            UserRelationship.from_user_id == current_user.id,
            UserRelationship.to_user_id == opponent_id)
            ).first()
    #DBから削除
    with db.session.begin(subtransactions=True):
        db.session.delete(lift)
    db.session.commit()
    return redirect(url_for('top'))


#フォロー一覧ページの処理
@app.route('/follow_state',methods=['GET','POST'])
@login_required
def follow_management():
    #UserDBとUserRelationshipDBでuser.idでに内部結合 フォローしているuserを取得
    follow_users = User.query.join(UserRelationship,
                    and_(
                    UserRelationship.from_user_id == current_user.id,
                    UserRelationship.to_user_id == User.id,  
                    ),).all()
    #UserDBとUserRelationshipDBでuser.idでに内部結合 フォロワーを取得
    follower_users = User.query.join(UserRelationship,
                    and_(
                    UserRelationship.from_user_id == User.id,
                    UserRelationship.to_user_id == current_user.id,  
                    ),).all()
    return render_template('follow_management.html',follow_users=follow_users,follower_users=follower_users)

#チャットの処理
@app.route('/chat/<friend_id>', methods=['GET','POST'])
@login_required
def chat(friend_id):
    
    friend = User.query.filter_by(id=friend_id).first()
    print(friend_id)
    print(friend)
    messages = Chat.query.filter(or_(
        and_(Chat.from_user_id==current_user.id,Chat.to_user_id==friend.id),
        and_(Chat.from_user_id==friend.id,Chat.to_user_id==current_user.id),
        )).all()
    print(messages)
    
    if request.method == 'POST':
        message = request.form.get('message')
        print(friend_id)
        print(message)
        new_message = Chat(from_user_id=current_user.id,to_user_id=friend_id,message=message)
        with db.session.begin(subtransactions=True):
            db.session.add(new_message)
        db.session.commit()
        return redirect(url_for('chat',friend_id=friend_id))
    
    return render_template('chat.html',friend=friend, messages=messages)



     