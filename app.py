# app.py 

# Auther: hhh5460
# Time: 2018/10/05
# Address: DongGuan YueHua

from functools import wraps
from flask import Flask, request, render_template, redirect, url_for, flash, session,json,jsonify

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_
from werkzeug.utils import secure_filename
import os
import random
from PIL import Image
import uuid

import base64
import sys
from typing import List
from antchain_sdk_appex.client import Client as APPEXClient
from antchain_sdk_appex import models as appex_models

UPLOAD_FOLDER = './static'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = '\xc9ixnRb\xe40\xd4\xa5\x7f\x03\xd0y6\x01\x1f\x96\xeao+\x8a\x9f\xe4'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)



# 定义ORM
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return '<User %r>' % self.username


class Project(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    projectname = db.Column(db.String(120))
    pic = db.Column(db.String(120))
    itmeBg = db.Column(db.String(200))
    itmeFace = db.Column(db.String(200))
    itmeEye = db.Column(db.String(200))
    itmeEar = db.Column(db.String(200))
    itmeNose = db.Column(db.String(200))
    itmeMouth = db.Column(db.String(200))
    whichChain = db.Column(db.String(50))

    def __repr__(self):
        return '<Project %r>' % self.projectname



# 创建表格、插入数据
@app.before_first_request
def create_db():
    print('第一次运行')
    db.drop_all()  # 每次运行，先删除再创建
    db.create_all()
    admin = User(username='admin', password='root', email='admin@example.com')
    dev = User(username='dev', password='dev', email='dev@example.com')
    db.session.add(admin)
    db.session.add(dev)
    db.session.commit()
    

############################################
# 辅助函数、装饰器
############################################

# 登录检验（用户名、密码验证）
def valid_login(username, password):
    user = User.query.filter(and_(User.username == username, User.password == password)).first()
    if user:
        return True
    else:
        return False


# 注册检验（用户名、邮箱验证）
def valid_regist(username, email):
    user = User.query.filter(or_(User.username == username, User.email == email)).first()
    if user:
        return False
    else:
        return True


#查询个人项目情况
def valid_proj(username):
    proj = Project.query.filter(Project.username == username).all()
    tmp = []
    for x in proj:
        tmp.append(x.__dict__)
    return tmp

# 登录
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # if g.user:
        if session.get('username'):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login', next=request.url)) # 
    return wrapper

# 检查上传图片合法性,上传图片

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#动态合成图片
def _compose_image(project_id):
    project = Project.query.filter(Project.id == project_id).first()
    itmeBg = project.itmeBg.split("|")
    itmeFace = project.itmeFace.split("|")
    itmeEye = project.itmeEye.split("|")
    itmeEar = project.itmeEar.split("|")
    itmeNose = project.itmeNose.split("|")
    itmeMouth = project.itmeMouth.split("|")
    itmeBg.pop()
    itmeFace.pop()
    itmeEye.pop()
    itmeEar.pop()
    itmeNose.pop()
    itmeMouth.pop()
    print(itmeBg)
    image_files = [random.choice(itmeBg),random.choice(itmeFace),random.choice(itmeEye),random.choice(itmeEar),random.choice(itmeNose),random.choice(itmeMouth)]
    print(image_files)
    composite = None
    for image_file in image_files:
        foreground = Image.open(image_file).convert("RGBA")
        if composite:
            composite = Image.alpha_composite(composite, foreground)
        else:
            composite = foreground
    output_path = "%s.png" % project_id
    composite.save(os.path.join(app.config['UPLOAD_FOLDER']+"/output/", output_path))
    #更新pic字段
    project.pic = os.path.join(app.config['UPLOAD_FOLDER']+"/output/", output_path)
    db.session.add(project)
    db.session.commit()
    #同步到蚂蚁链
    #goToMayi(project.pic)

#同步存储到蚂蚁链
def create_client():
    config = appex_models.Config()
    # 您的AccessKey ID
    config.access_key_id = "LTAI5tDp7PsufMj8usZ6sdLc"
    # 您的AccessKey Secret
    config.access_key_secret = "wQSlKuHOQF8XcRCALgx8fg9vQ69KE3"
    config.endpoint = "https://openapi.antchain.antgroup.com/gateway.do"
    return APPEXClient(config)

def base64Img(file):
    with open(file, "rb") as img_file:
        base64Str = base64.b64encode(img_file.read()).decode('utf-8')
        return base64Str

def goToMayi(file):
    base64Imgs = base64Img(file)
    client = create_client()
    init_solution_filenotary_request = appex_models.InitSolutionFilenotaryRequest(
        app_did='did:mychain:d4bcba1bde29e5b6c32e4c643ee5680ab2ef79b72d5aac5d32e2c6057afb913b'
    )
    result = client.init_solution_filenotary(init_solution_filenotary_request)
    print(result)







############################################
# 路由
############################################

# 1.主页
@app.route('/')
def home():
    project = valid_proj(session.get('username'))
    return render_template('home.html', username=session.get('username'),project=project)

# 2.登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'], request.form['password']):
            flash("成功登录！")
            session['username'] = request.form.get('username')
            return redirect(url_for('home'))
        else:
            error = '错误的用户名或密码！'

    return render_template('login.html', error=error)

# 3.注销
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# 4.注册
@app.route('/regist', methods=['GET','POST'])
def regist():
    error = None
    if request.method == 'POST':
        if request.form['password1'] != request.form['password2']:
            error = '两次密码不相同！'
        elif valid_regist(request.form['username'], request.form['email']):
            user = User(username=request.form['username'], password=request.form['password1'], email=request.form['email'])
            db.session.add(user)
            db.session.commit()
            
            flash("成功注册！")
            return redirect(url_for('login'))
        else:
            error = '该用户名或邮箱已被注册！'
    
    return render_template('regist.html', error=error)

# 5.个人中心
@app.route('/panel')
@login_required
def panel():
    username = session.get('username')
    user = User.query.filter(User.username == username).first()
    return render_template("panel.html", user=user)

#6.创建新项目
@app.route('/creat_project', methods=['GET','POST'])
@login_required
def creat_project():
    error = None
    if request.method == 'POST':
        username = session.get('username')
        user = User.query.filter(User.username == username).first()
        #处理前端表单数据
        itmeBg = request.form['background']
        itmeFace = request.form['face']
        itmeEye = request.form['eye']
        itmeEar = request.form['ear']
        itmeNose = request.form['nose']
        itmeMouth = request.form['mouth']
        project = Project(username = user.username,email = user.email,projectname=request.form['projectname'],itmeBg=itmeBg,itmeFace=itmeFace,itmeEye=itmeEye,itmeEar=itmeEar,itmeNose=itmeNose,itmeMouth=itmeMouth)
        db.session.add(project)
        db.session.commit()
        flash("添加项目成功！")
        #根据插入的prjocetid去合成一张效果图
        _compose_image(project.id)
        return redirect(url_for('home'))
    return render_template('creat_project.html', error=error)

#7.上传图片
@app.route('/upload/<path:url_path>', methods=['GET','POST'])
@login_required
def upload_file(url_path):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER']+"/"+url_path, filename))
            return os.path.join(app.config['UPLOAD_FOLDER']+"/"+url_path, filename)
    return '404'

#预览生成
@app.route('/preview', methods=['GET','POST'])
def preview():
    if request.method == 'POST':
        composite = None
        arr = request.form['data']
        print('-------')
        print(arr)
        print(type(arr))
        arr = arr.split(",")
        print('-------')
        print(arr)
        for image_file in arr:
            foreground = Image.open(image_file).convert("RGBA")
            if composite:
                composite = Image.alpha_composite(composite, foreground)
            else:
                composite = foreground
        output_path = "test_%s.png" % uuid.uuid1()
        composite.save(os.path.join(app.config['UPLOAD_FOLDER'] + "/output/", output_path))
        print('---------')
        print(os.path.join(app.config['UPLOAD_FOLDER'] + "/output/", output_path))
        return os.path.join(app.config['UPLOAD_FOLDER'] + "/output/", output_path)

if __name__ == '__main__':
    app.run(debug = True)
    #app.run(host="0.0.0.0")
