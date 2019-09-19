#coding:utf8

from flask import Blueprint,render_template,redirect,url_for,flash,session,request,g,jsonify
from app.home.forms import RegistForm,LoginForm,UserdetailForm,PwdForm,CommentForm
from app.models import User,Userlog,Preview,Tag,Movie,Comment,Moviecol
from app.exts import db
import uuid
from functools import wraps
from app.admin.views import change_filename
from werkzeug.utils import secure_filename
import os
from app.config import DevConfig

bp=Blueprint('home',__name__)


@bp.before_request
def my_before_request():
    user_id=session.get('user_id')
    if user_id:
        user=User.query.filter(User.id==user_id).first()
        if user:
            g.user=user

@bp.context_processor
def my_context_processor():
    if hasattr(g, 'user'):
        return {'g_user': g.user}
    return {}

# 定义登录判断装饰器
def user_login_require(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # session不存在时请求登录
        if "user" in session:
            return f(*args,**kwargs)
        return redirect(url_for("home.login", next=request.url))
    return decorated_function

@bp.route('/animation/')
def animation():
    data=Preview.query.all()
    return render_template('home/animation.html',data=data)

@bp.route('/')
def new_index():
    return redirect(url_for('home.index',page=1))

@bp.route('/<int:page>')
def index(page=None):
    tags = Tag.query.all()
    page_data = Movie.query
    # 通过url获取参数
    tid = request.args.get("tid", 0)

    if int(tid)!=0:
        page_data=page_data.filter_by(tag_id=int(tid))

    star = request.args.get("star",0)
    if int(star)!=0:
        page_data=page_data.filter_by(star=int(star))

    time = request.args.get("time",0)
    if int(time) != 0:
        if int(time) == 1:
            page_data=page_data.order_by(Movie.addtime.desc())
        else:
            page_data=page_data.order_by(Movie.addtime.asc())

    pm = request.args.get("pm",0)
    if int(pm) != 0:
        if int(pm) == 1:
            page_data=page_data.order_by(Movie.playnum.desc())
        else:
            page_data=page_data.order_by(Movie.playnum.asc())

    cm = request.args.get("cm",0)
    if int(cm) != 0:
        if int(time) == 1:
            page_data=page_data.order_by(Movie.commentnum.desc())
        else:
            page_data=page_data.order_by(Movie.commentnum.asc())


    # 保存获取的参数
    p = dict(
        tid=tid,
        star=star,
        time=time,
        pm=pm,
        cm=cm
    )



    # 分页处理
    if page is None:
        page=1

    page_data = page_data.paginate(page=page, per_page=DevConfig.PAGE_SET)

    return render_template("home/index.html", tags=tags, p=p, page_data=page_data)


@bp.route('/login/',methods=['POST','GET'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        name=form.name.data
        user=User.query.filter_by(name=name).first()

        if user and user.pwd == form.pwd.data:
            flash('登陆成功','ok')
            session['user']=user.name
            session['user_id']=user.id


            userlog=Userlog(user_id=user.id,ip=request.remote_addr)
            db.session.add(userlog)
            db.session.commit()

            return redirect(url_for('home.user'))
        else:
            flash('账号或密码错误','err')
    return render_template('home/login.html',form=form)


@bp.route('/logout/')
@user_login_require
def logout():
    session.pop('user', None)
    session.pop("user_id", None)
    return redirect(url_for('home.login'))


@bp.route('/register/',methods=['POST','GET'])
def register():
    form=RegistForm()
    if form.validate_on_submit():
        data=form.data
        user=User(
            name=data['name'],
            email=form.email.data,
            phone=form.phone.data,
            pwd=form.pwd.data,
            uuid= uuid.uuid4().hex
        )
        db.session.add(user)
        db.session.commit()
        flash('注册成功','ok')
        return redirect(url_for('home.login'))
    return render_template('home/register.html',form=form)


@bp.route('/user/',methods=['POST','GET'])
@user_login_require
def user():
    form = UserdetailForm()
    user = User.query.get(int(session["user_id"]))
    if user.face is not None:
        form.face.validators = []
    if request.method == "GET":
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    if form.validate_on_submit():
        data = form.data

        if not os.path.exists(DevConfig.UP_DIR + "users" + os.sep):
            os.makedirs(DevConfig.UP_DIR + "users" + os.sep)
            os.chmod(DevConfig.UP_DIR + "users" + os.sep, "rw")

        if form.face.data.filename != '':
            old_face = user.face
            file_face = secure_filename(form.face.data.filename)
            user.face = change_filename(file_face)
            form.face.data.save(DevConfig.UP_DIR + "users" + os.sep + user.face)
            if old_face is not None and os.path.exists(DevConfig.UP_DIR + "users" + os.sep + old_face):
                os.remove(DevConfig.UP_DIR + "users" + os.sep + old_face)

        user.name = data["name"]
        user.email = data["email"]
        user.phone = data["phone"]
        user.info = data["info"]
        db.session.add(user)
        db.session.commit()
        flash("修改成功！", "ok")
    return render_template("home/user.html", form=form, user=user)


@bp.route('/pwd/',methods=['POST','GET'])
@user_login_require
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=session["user"]).first()
        user.pwd = data['new_pwd']
        db.session.add(user)
        db.session.commit()
        session.pop('user', None)
        session.pop("user_id", None)
        flash("修改密码成功，请重新登录！", "ok")
        return redirect(url_for("home.logout"))
    return render_template("home/pwd.html", form=form)


@bp.route('/comments/<int:page>')
@user_login_require
def comments(page=None):
    if page is None:
        page=1
    page_data = Comment.query.filter_by(user_id=g.user.id).\
        order_by(Comment.addtime.desc()).paginate(page=page,per_page=DevConfig.PAGE_SET)
    return render_template('home/comments.html',page_data=page_data)


@bp.route('/loginlog/<int:page>')
@user_login_require
def loginlog(page=None):
    if page is None:
        page=1
    page_data=Userlog.query.\
        filter_by(user_id=int(session['user_id'])).\
        order_by(Userlog.addtime.desc()).paginate(page=page,per_page=DevConfig.PAGE_SET)
    return render_template('home/loginlog.html',page_data=page_data)

@bp.route('/moviecol/add/')
@user_login_require
def moviecol_add():
    uid=request.args.get('uid','')
    mid=request.args.get('mid','')
    moviecol=Moviecol.query.filter_by(user_id=int(uid),movie_id=int(mid)).count()
    print(uid,mid,moviecol)
    if moviecol==1:
        data=dict(ok=0)

    elif moviecol==0:
        moviecol = Moviecol(user_id=int(uid),movie_id=int(mid))
        data=dict(ok=1)
        db.session.add(moviecol)
        db.session.commit()

    return jsonify(data)

@bp.route('/moviecol/<int:page>')
@user_login_require
def moviecol(page=None):
    if page is None:
        page=1
    page_data=Moviecol.query.filter_by(user_id=g.user.id).order_by(Moviecol.addtime.desc()).paginate(page=page,per_page=DevConfig.PAGE_SET)
    return render_template('home/moviecol.html',page_data=page_data)


@bp.route('/search/<int:page>')
def search(page):
    if page is None:
        page=1
    key=request.args.get('key','')
    key_count=Movie.query.filter(Movie.title.ilike('%' + key + '%')).count()
    page_data=Movie.query.filter(Movie.title.ilike('%'+key+'%')).\
        order_by(Movie.addtime.desc()).paginate(page=page,per_page=DevConfig.PAGE_SET)
    page_data.key=key
    return render_template('home/search.html',key=key,page_data=page_data,key_count=key_count)


@bp.route('/play/<int:id>/<int:page>',methods=['POST','GET'])
@user_login_require
def play(id=None,page=None):
    if page is None:
        page=1
    movie=Movie.query.get_or_404(int(id))
    form=CommentForm()

    if 'user' in session and form.validate_on_submit():
        comment=Comment(content=form.content.data,movie_id=movie.id,user_id=session['user_id'])
        db.session.add(comment)
        db.session.commit()
        movie.commentnum = movie.commentnum + 1
        db.session.add(movie)
        db.session.commit()

        flash('添加评论成功','ok')
        return redirect(url_for('home.play',id=movie.id,page=1))

    movie.playnum = movie.playnum + 1
    db.session.add(movie)
    db.session.commit()

    page_data = Comment.query.filter_by(movie_id=movie.id).order_by(Comment.addtime.desc()).paginate(page=page, per_page=5)
    return render_template('home/play.html',movie=movie,form=form,page_data=page_data)






