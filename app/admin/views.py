#coding:utf8

from flask import Blueprint,render_template,redirect,url_for,request,flash,session,abort
from .forms import LoginForm,TagForm,MovieForm,PreviewForm,PwdForm,AuthForm,RoleForm,AdminForm
from app.models import Admin,Tag,Movie,Preview,User,Comment,Moviecol,Oplog,Adminlog,Userlog,Auth,Role
from functools import wraps
from app.exts import db
from app.config import DevConfig
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
from app.config import DevConfig
from flask_wtf.file import FileAllowed




bp=Blueprint('admin',__name__,url_prefix='/admin')
page_data = None       # 存储分页数据以便返回使用
edit_role_name = None  # 存储编辑角色页的旧角色名称

@bp.context_processor
def tpl_extra():
    # if "admin_id" in session and Adminlog.query.filter_by(admin_id=session["admin_id"]).count() > 0:
    #     adminlog = Adminlog.query.filter_by(admin_id=session["admin_id"]).order_by(
    #         Adminlog.addtime.desc()
    #     ).first()
    #     login_time = adminlog.addtime
    # else:
    #     # 登陆前是看不到页面的，所以给空值
    #     login_time = None

    data = dict(
        login_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    return data


# 定义登录判断装饰器
def admin_login_require(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # session不存在时请求登录
        if "admin" in session:
            return f(*args,**kwargs)
        return redirect(url_for("admin.login", next=request.url))

    return decorated_function



# 定义权限控制装饰器
def admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" in session:
            # 查询出权限ID，然后查出对应的路由地址
            admin = Admin.query.join(Role).filter(
                Admin.role_id == Role.id,
                Admin.id == session["admin_id"]
            ).first()
            auths = list(map(lambda v: int(v), admin.role.auths.split(",")))
            auth_list = Auth.query.all()
            urls = [v.url for v in auth_list for var in auths if var == v.id]
            rule= request.url_rule
            # 判断是否有权限访问
            if DevConfig.AUTH_SWITCH and str(rule) not in urls:
                abort(404)
        return f(*args, **kwargs)

    return decorated_function

@bp.route('/')
@admin_login_require
def index():
    return render_template('admin/index.html')

@bp.route('/login/',methods=['POST','GET'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        account_information=form.account.data
        admin=Admin.query.filter_by(name=account_information).first()
        if not admin or not admin.check_pwd(form.pwd.data):
            flash('账号或密码错误')
            return redirect(url_for('admin.login'))
        session['admin']=account_information
        session["admin_id"] = admin.id
        adminlog = Adminlog(
            admin_id=admin.id,
            ip=request.remote_addr
        )
        db.session.add(adminlog)
        db.session.commit()
        #当用户请求重定向到登入视图，它的请求字符串中会有一个next变量，
        # 其值为用户之前访问的页面，因此在我们完成验证之后，
        # 我们通过request.args.get(“next”)获取到用户之前访问的页面地址，
        # 并进行重定向，注意建议对此参数进行安全校验，避免重定向攻击，我有一个验证安全链接的py模块，但这里不想贴了。。。
        return redirect(request.args.get('next') or url_for('admin.index'))
    return render_template('admin/login.html',form=form)

@bp.route('/logout/')
def logout():
    print(session,'清除前')
    session.pop('admin',None)
    session.pop("admin_id",None)
    print(session,'清除后')
    return redirect(url_for('admin.login'))

@bp.route('/pwd/',methods=['POST','GET'])
@admin_login_require
def pwd():
    form= PwdForm()
    if form.validate_on_submit():
        account_information=session['admin']
        admin = Admin.query.filter_by(name=account_information).first()
        if admin:
            if admin.pwd != form.old_pwd.data:
                flash('你输入了错误的旧密码','err')
                return redirect(url_for('admin.pwd'))
            elif admin.pwd == form.old_pwd.data and form.old_pwd.data == form.new_pwd.data:
                flash('新旧密码不能一致', 'err')
                return redirect(url_for('admin.pwd'))
            else:
                flash('修改成功', 'ok')
                admin.pwd = form.new_pwd.data
                db.session.add(admin)
                db.session.commit()
                return redirect(url_for('admin.pwd'))
        else:
            redirect(url_for('admin.login'))
    return render_template('admin/pwd.html',form=form)

@bp.route('/tag/add/',methods=['POST','GET'])
@admin_login_require
def tag_add():
    form=TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data["name"]).count()
        if tag == 1:
            flash("名称已经存在！", "err")
            return redirect(url_for("admin.tag_add"))
        tag = Tag(name=data["name"])
        db.session.add(tag)
        db.session.commit()
        flash("添加标签成功！", "ok")
        oplog = Oplog(admin_id=session["admin_id"],ip=request.remote_addr,reason="添加新标签：%s" % data["name"])
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.tag_add"))
    return render_template('admin/tag_add.html',form=form)

@bp.route('/tag/list/<int:page>/')
@admin_login_require
def tag_list(page = None):

    if page is None:
        page = 1
    page_data = Tag.query.order_by(Tag.addtime.desc()).paginate(page=page, per_page=DevConfig.PAGE_SET)
    return render_template("admin/tag_list.html", page_data=page_data)


# 定义标签删除视图
@bp.route("/tag/del/<int:id>/", methods=["GET"])
@admin_login_require
def tag_del(id=None):
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash("删除标签成功！", "ok")
    return redirect(url_for("admin.tag_list", page=1))

# 定义编辑标签视图
@bp.route("/tag/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_require
def tag_edit(id=None):
    form = TagForm()
    tag = Tag.query.get_or_404(id)
    page = page_data.page if page_data is not None else 1
    if form.validate_on_submit():
        data = form.data
        tag_count = Tag.query.filter_by(name=form.name.data).count()
        if tag_count == 1 and tag.name != form.name.data:
            flash("名称已经存在！", "err")
            return redirect(url_for("admin.tag_edit", id=id))

        tag.name = form.name.data
        db.session.add(tag)
        db.session.commit()
        flash("修改标签成功！", "ok")
        return redirect(url_for("admin.tag_list", page=page))
    return render_template("admin/tag_edit.html", form=form, tag=tag)

def change_filename(filename):
    fileinfo = os.path.splitext(filename)  # 对名字进行前后缀分离
    filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex + fileinfo[-1]  # 生成新文件名,fileinfo[-1]是后缀名
    return filename

@bp.route('/movie/add/',methods=['POST','GET'])
@admin_login_require
def movie_add():
    form=MovieForm()
    form.tag_id.choices=[(0,'未选择')]+[(v.id,v.name) for v in Tag.query.all()]
    if form.validate_on_submit():
        if Movie.query.filter_by(title=form.title.data).first():
            flash('影片已经存在','err')
            return redirect(url_for('admin.movie_add'))

        file_url = change_filename(form.url.data.filename)
        file_logo=change_filename(form.logo.data.filename)
        url=secure_filename(file_url)
        logo=secure_filename(file_logo)

        if not os.path.exists((DevConfig.UP_DIR)):
            os.makedirs(DevConfig.UP_DIR)
        UPLOAD_PATH=DevConfig.UP_DIR

        form.url.data.save(os.path.join(UPLOAD_PATH,url))
        form.logo.data.save(os.path.join(UPLOAD_PATH,logo))
        movie=Movie(
            title=form.title.data,
            url=url,
            info=form.info.data,
            logo=logo,
            star=int(form.star.data),
            playnum=0,
            commentnum=0,
            tag_id=int(form.tag_id.data),
            area=form.area.data,
            release_time=form.release_time.data,
            length=form.length.data
        )
        db.session.add(movie)
        db.session.commit()
        flash('添加成功','ok')
        return redirect(url_for('admin.movie_list',page=1))
    return render_template('admin/movie_add.html',form=form)


@bp.route('/movie/list/<int:page>',methods=['GET'])
@admin_login_require
def movie_list(page = None):
    global page_data
    if page is None:
        page = 1
    page_data = Movie.query.order_by(Movie.addtime.desc()).paginate(page=page,per_page=DevConfig.PAGE_SET)
    return render_template('admin/movie_list.html',page_data=page_data)



@bp.route("/movie/del/<int:id>/", methods=["GET"])
@admin_login_require
def movie_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    movie = Movie.query.filter_by(id=id).first_or_404()
    db.session.delete(movie)
    db.session.commit()

    print(os.path.exists(DevConfig.UP_DIR + movie.url),'ttt')
    print(os.path.exists(DevConfig.UP_DIR + movie.logo),'qqq')

    if os.path.exists(DevConfig.UP_DIR + movie.url):  # 删除文件
        os.remove(DevConfig.UP_DIR + movie.url)
    if os.path.exists(DevConfig.UP_DIR + movie.logo):
        os.remove(DevConfig.UP_DIR + movie.logo)
    flash("删除视频成功！", "ok")
    return redirect(url_for("admin.movie_list", page=page))

# 定义编辑视频视图
@bp.route("/movie/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_require
def movie_edit(id=None):
    form = MovieForm()
    form.tag_id.choices = [(0, "未选择")] + [(v.id, v.name) for v in Tag.query.all()]

    form.url.validators = [FileAllowed(['mp4','avi'],message='只能上传mp4和avi')]  # 因为可以不做更改，所以不需要校验
    form.logo.validators = [FileAllowed(['jpg','png','jpeg'],message='只能上传jpg和png')]

    movie = Movie.query.get_or_404(id)
    page = page_data.page if page_data is not None else 1
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title=data["title"]).count()
        if movie_count == 1 and movie.title != data['title']:
            flash("片名已经存在！", "err")
            return redirect(url_for("admin.movie_edit", id=id))

        if not os.path.exists(DevConfig.UP_DIR):  # 存放目录不存在则创建
            os.makedirs(DevConfig.UP_DIR)
            os.chmod(DevConfig.UP_DIR, "rw")

        if form.url.data.filename != '':
            old_url = movie.url
            file_url = change_filename(form.url.data.filename)  # 调用函数生成新的文件名
            movie.url = secure_filename(file_url)  # 获取并转化为安全的视频文件名
            form.url.data.save(DevConfig.UP_DIR + movie.url)  # 保存上传的数据
            if os.path.exists(DevConfig.UP_DIR + old_url):  # 删除旧文件
                os.remove(DevConfig.UP_DIR + old_url)

        if form.logo.data.filename != '':
            old_logo = movie.logo
            file_logo = change_filename(form.logo.data.filename)
            movie.logo = secure_filename(file_logo)
            form.logo.data.save(DevConfig.UP_DIR + movie.logo)
            if os.path.exists(DevConfig.UP_DIR + old_logo):
                os.remove(DevConfig.UP_DIR + old_logo)


        movie.title = data["title"]
        movie.info = data["info"]
        movie.star = int(data["star"])
        movie.tag_id = int(data["tag_id"])
        movie.area = data["area"]
        movie.release_time = data["release_time"]
        movie.length = data["length"]
        db.session.add(movie)
        db.session.commit()
        flash("修改视频成功！", "ok")
        return redirect(url_for("admin.movie_list", page=page))
    return render_template("admin/movie_edit.html", form=form, movie=movie)

@bp.route('/preview/add/',methods=['POST','GET'])
@admin_login_require
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        preview = Preview.query.filter_by(title=form.title.data).count()
        if preview == 1:
            flash("预告标题已经存在！", "err")
            return redirect(url_for("admin.preview_add"))
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(DevConfig.UP_DIR):
            os.makedirs(DevConfig.UP_DIR)
            os.chmod(DevConfig.UP_DIR, "rw")
        logo = change_filename(file_logo)
        form.logo.data.save(DevConfig.UP_DIR + logo)
        preview = Preview(title=data["title"],logo=logo)
        db.session.add(preview)
        db.session.commit()
        flash("添加预告成功！", "ok")
        return redirect(url_for("admin.preview_list",page=1))
    return render_template("admin/preview_add.html", form=form)

@bp.route('/preview/list/<int:page>/')
@admin_login_require
def preview_list(page = None):
    global page_data
    if page is None:
        page = 1
    page_data = Preview.query.order_by(Preview.addtime.desc()).paginate(page=page,per_page=DevConfig.PAGE_SET)
    return render_template('admin/preview_list.html',page_data=page_data)

# 定义预览图删除视图
@bp.route("/preview/del/<int:id>/", methods=["GET"])
@admin_login_require
def preview_del(id=None):

    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1

    preview = Preview.query.filter_by(id=id).first_or_404()
    db.session.delete(preview)
    db.session.commit()

    if os.path.exists(DevConfig.UP_DIR + preview.logo):  # 删除文件
        os.remove(DevConfig.UP_DIR + preview.logo)

    flash("删除预告照片成功！", "ok")
    return redirect(url_for("admin.preview_list",page=page))

@bp.route('/preview/edit/<int:id>',methods=['POST','GET'])
@admin_login_require
def preview_edit(id=None):
    form=PreviewForm()
    form.logo.validators=[FileAllowed(['jpg','png','gif'])]
    preview=Preview.query.get_or_404(id)

    page=page_data.page if page_data is not None else 1

    if form.validate_on_submit():
        preview_count= Preview.query.filter_by(title=form.title.data).count()
        print(preview_count)
        if preview_count and preview.title != form.title.data:
            flash('你输入了重复的内容','err')
            return redirect(url_for('admin.preview_edit',id=id))

        if not os.path.exists(DevConfig.UP_DIR):
            os.makedirs(DevConfig.UP_DIR)

        if form.logo.data.filename != '':
            old_name = preview.logo
            new_name = change_filename(form.logo.data.filename)
            preview.logo = secure_filename(new_name)
            form.logo.data.save(DevConfig.UP_DIR+preview.logo)

            if os.path.exists(DevConfig.UP_DIR+old_name):
                os.remove(DevConfig.UP_DIR+old_name)

        preview.title=form.title.data

        db.session.add(preview)
        db.session.commit()
        flash('你修改成功','ok')

        return redirect(url_for('admin.preview_list',page=page))
    return render_template('admin/preview_edit.html',form=form,preview=preview)




#
# # 定义编辑预览图视图
# @bp.route("/preview/edit/<int:id>/", methods=["GET", "POST"])
# @admin_login_require
# def preview_edit(id=None):
#     form = PreviewForm()
#     form.logo.validators = [FileAllowed(['jpg','png'],message='只能上传jpg和png')]  # 因为可以不做更改，所以不需要校验
#
#     preview = Preview.query.get_or_404(id)
#     page = page_data.page if page_data is not None else 1
#     if form.validate_on_submit():
#         data = form.data
#         preview_count = Preview.query.filter_by(title=form.title.data).count()
#         if preview_count == 1 and preview.title != form.title.data:
#             flash("片名已经存在！", "err")
#             return redirect(url_for("admin.preview_edit", id=id))
#
#         if not os.path.exists(DevConfig.UP_DIR):  # 存放目录不存在则创建
#             os.makedirs(DevConfig.UP_DIR)
#             os.chmod(DevConfig.UP_DIR, "rw")
#
#         if form.logo.data.filename != '':
#             old_logo = preview.logo
#             file_logo = change_filename(form.logo.data.filename)  # 调用函数生成新的文件名
#             preview.logo= secure_filename(file_logo)  # 获取并转化为安全的视频文件名
#             form.logo.data.save(DevConfig.UP_DIR + preview.logo)  # 保存上传的数据
#
#             if os.path.exists(DevConfig.UP_DIR + old_logo):  # 删除旧文件
#                 os.remove(DevConfig.UP_DIR + old_logo)
#
#         preview.title=form.title.data
#
#         db.session.add(preview)
#         db.session.commit()
#         flash("修改预告片成功！", "ok")
#         return redirect(url_for("admin.preview_list", page=page))
#     return render_template("admin/preview_edit.html", form=form,preview=preview)

@bp.route('/user/view/<int:id>')
@admin_login_require
def user_view(id):
    user=User.query.get_or_404(id)
    return render_template('admin/user_view.html',user=user)

@bp.route('/user/list/<int:page>')
@admin_login_require
def user_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = User.query.order_by(User.addtime.desc()).paginate(page=page, per_page=DevConfig.PAGE_SET)
    return render_template("admin/user_list.html", page_data=page_data)

@bp.route("/user/del/<int:id>/", methods=["GET"])
@admin_login_require
def user_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1

    user = User.query.filter_by(id=id).first_or_404()
    db.session.delete(user)
    db.session.commit()
    # if os.path.exists(DevConfig.UP_DIR + "users" + os.sep + user.face):
    #     os.remove(DevConfig.UP_DIR + "users" + os.sep + user.face)
    flash("删除会员成功！", "ok")

    return redirect(url_for("admin.user_list", page=page))

@bp.route('/comment/list/<int:page>')
@admin_login_require
def comment_list(page):
    global page_data
    if page is None:
        page = 1
    # page_data = Comment.query.join(Movie).join(User).filter(
    #     Comment.movie_id == Movie.id,
    #     Comment.user_id == User.id
    # ).order_by(
    #     Comment.addtime.desc()
    # ).paginate(page=page, per_page=DevConfig.PAGE_SET)
    page_data = Comment.query.order_by(Comment.addtime.desc()).paginate(page=page,per_page=DevConfig.PAGE_SET)
    return render_template("admin/comment_list.html", page_data=page_data)

@bp.route('/comment/del/<int:id>')
@admin_login_require
def comment_del(id=None):
    comment=Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash('删除评论成功','ok')
    return redirect(url_for('admin.comment_list',page=1))


@bp.route('/moviecol/list/<int:page>')
@admin_login_require
def moviecol_list(page):
    global page_data
    if page is None:
        page = 1
    page_data = Moviecol.query.order_by(Moviecol.addtime.desc()).paginate(page=page, per_page=DevConfig.PAGE_SET)
    return render_template('admin/moviecol_list.html',page_data=page_data)

@bp.route('/moviecol/del/<int:id>')
@admin_login_require
def moviecol_del(id=None):
    col=Moviecol.query.get_or_404(id)
    db.session.delete(col)
    db.session.commit()
    flash('删除收藏成功','ok')
    return redirect(url_for('admin.moviecol_list',page=1))

@bp.route('/oplog/list/<int:page>')
@admin_login_require
def oplog_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Oplog.query.join(Admin).filter(
        Oplog.admin_id == Admin.id
    ).order_by(
        Oplog.addtime.desc()
    ).paginate(page=page, per_page=DevConfig.PAGE_SET)
    return render_template("admin/oplog_list.html", page_data=page_data)

@bp.route('/adminloginlog/list/<int:page>')
@admin_login_require
def adminloginlog_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Adminlog.query.join(Admin).filter(Adminlog.admin_id == Admin.id).order_by(Adminlog.addtime.desc())\
        .paginate(page=page, per_page=DevConfig.PAGE_SET)
    return render_template("admin/adminloginlog_list.html", page_data=page_data)

@bp.route('/userloginlog/list/<int:page>')
@admin_login_require
def userloginlog_list(page):
    global page_data
    if page is None:
        page = 1
    page_data = Userlog.query.order_by(Userlog.addtime.desc()
    ).paginate(page=page, per_page=DevConfig.PAGE_SET)
    return render_template("admin/userloginlog_list.html", page_data=page_data)

@bp.route('/auth/add',methods=['POST','GET'])
@admin_login_require
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(name=data["name"],url=data["url"])
        db.session.add(auth)
        db.session.commit()
        flash("添加权限成功！", "ok")
        oplog = Oplog(admin_id=session["admin_id"],ip=request.remote_addr,reason="添加新权限：%s" % data["name"])
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.auth_list",page=1))
    return render_template("admin/auth_add.html", form=form)


@bp.route('/auth/list/<int:page>')
@admin_login_require
def auth_list(page):
    global page_data
    if page is None:
        page = 1
    page_data = Auth.query.order_by(
        Auth.addtime.desc()
    ).paginate(page=page, per_page=DevConfig.PAGE_SET)
    return render_template("admin/auth_list.html", page_data=page_data)

# 定义权限删除视图
@bp.route("/auth/del/<int:id>/", methods=["GET"])
@admin_login_require
def auth_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    auth = Auth.query.filter_by(id=id).first_or_404()
    db.session.delete(auth)
    db.session.commit()
    flash("删除权限成功！", "ok")
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除权限：%s" % auth.name
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for("admin.auth_list", page=page))


@bp.route("/auth/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_require
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.get_or_404(id)
    page = page_data.page if page_data is not None else 1
    if form.validate_on_submit():
        data = form.data
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="修改权限：%s（原名：%s）" % (data["name"], auth.name)
        )
        db.session.add(oplog)
        db.session.commit()

        auth.name = form.name.data
        auth.url = form.url.data
        db.session.add(auth)
        db.session.commit()
        flash("修改权限成功！", "ok")
        return redirect(url_for("admin.auth_list", page=page))
    return render_template("admin/auth_edit.html", form=form, auth=auth)

@bp.route('/role/add',methods=['POST','GET'])
@admin_login_require
def role_add():
    form= RoleForm()
    form.auths.choices=[(0, '未选择')]+ [(v.id, v.name) for v in Auth.query.all()]

    print(form.auths.choices,'草草草')
    if form.validate_on_submit():
        data=form.data
        role = Role(
            name=data["name"],
            auths=",".join(map(lambda v: str(v), data["auths"]))
        )
        db.session.add(role)
        db.session.commit()
        flash("添加角色成功！", "ok")
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="添加新角色：%s" % data["name"]
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.role_add"))

    return render_template('admin/role_add.html',form=form)

@bp.route('/role/list/<int:page>')
@admin_login_require
def role_list(page):
    global page_data
    if page is None:
        page = 1
    page_data = Role.query.order_by(
        Role.addtime.desc()
    ).paginate(page=page, per_page=DevConfig.PAGE_SET)
    return render_template("admin/role_list.html", page_data=page_data)

# 定义角色删除视图
@bp.route("/role/del/<int:id>/", methods=["GET"])
@admin_login_require
def role_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    role = Role.query.filter_by(id=id).first_or_404()
    db.session.delete(role)
    db.session.commit()
    flash("删除角色成功！", "ok")
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除角色：%s" % role.name
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for("admin.role_list", page=page))

# 定义编辑角色视图
@bp.route("/role/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_require
def role_edit(id=None):
    global edit_role_name
    form = RoleForm()
    form.auths.choices = [(0, '未选择')] + [(v.id, v.name) for v in Auth.query.all()]
    role = Role.query.get_or_404(id)
    edit_role_name = role.name
    page = page_data.page if page_data is not None else 1
    if request.method == "GET":
        form.name.data = role.name
        form.auths.data = list(map(lambda v: int(v), role.auths.split(",")))
    if form.validate_on_submit():
        data = form.data
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="修改角色：%s（原名：%s）" % (data["name"], role.name)
        )
        db.session.add(oplog)
        db.session.commit()

        role.name = data["name"]
        role.auths = ",".join(map(lambda v: str(v), data["auths"]))
        db.session.add(role)
        db.session.commit()
        flash("修改角色成功！", "ok")
        return redirect(url_for("admin.role_list", page=page))
    return render_template("admin/role_edit.html", form=form, role=role,page=page)


# 定义添加管理员视图
@bp.route("/admin/add/", methods=["GET", "POST"])
@admin_login_require
def admin_add():
    form = AdminForm()
    form.role_id.choices=[(0, "未选择")] + [(v.id, v.name) for v in Role.query.all()]
    if form.validate_on_submit():
        data = form.data
        admin = Admin(
            name=data["name"],
            pwd=form.pwd.data,
            role_id=data["role_id"],
            is_super=1
        )
        db.session.add(admin)
        db.session.commit()
        flash("添加管理员成功！", "ok")
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="添加新管理员：%s" % data["name"]
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.admin_add"))
    return render_template("admin/admin_add.html", form=form)


# 定义管理员列表视图
@bp.route("/admin/list/<int:page>/", methods=["GET", "POST"])
@admin_login_require
def admin_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Admin.query.join(Role).filter(
        Admin.role_id == Role.id
    ).order_by(
        Admin.addtime.desc()
    ).paginate(page=page, per_page=DevConfig.PAGE_SET)
    return render_template("admin/admin_list.html", page_data=page_data)

