from wtforms import (StringField, PasswordField, SubmitField, FileField,
                     TextAreaField, SelectField, SelectMultipleField)
from wtforms.validators import DataRequired, ValidationError, EqualTo,InputRequired
from app.models import Admin, Tag, Auth, Role
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed,FileRequired




class LoginForm(FlaskForm):
    """管理员登录表单"""
    account = StringField(label="账号",validators=[DataRequired("请输入账号！")],
                          description="账号",
                          render_kw={ "class": "form-control","placeholder": "请输入账号！" })
    pwd = PasswordField(label="密码",validators=[DataRequired("请输入密码！")],
                        description="密码",
                        render_kw={"class": "form-control","placeholder": "请输入密码！", })
    submit = SubmitField('登录',
                         render_kw={ "class": "btn btn-primary btn-block btn-flat"})

    # # 账号验证，但是这种写法超级蠢，相当于差了两次数据库，实际上在视图函数里就可以了
    # def validate_account(self, field):
    #     account = field.data
    #     admin = Admin.query.filter_by(name=account).count()
    #     if admin == 0:
    #         raise ValidationError("账号不存在！")

class TagForm(FlaskForm):
    """标签表单"""
    name = StringField(label="名称",validators=[DataRequired("请输入标签名称！")],description="标签",
                       render_kw={"class": "form-control","id":
                           "input_name", "autofocus": "","placeholder": "请输入标签名称！"})
    submit = SubmitField('提交',
                         render_kw={"class": "btn btn-primary"})




class MovieForm(FlaskForm):
    """视频表单"""
    title = StringField(label="片名",validators=[DataRequired("请输入片名！")],description="片名",
                        render_kw={"class": "form-control","id": "input_title",
                                   "autofocus": "","placeholder": "请输入片名！"})
    url = FileField(label="文件",
                    validators=[FileRequired("请上传文件！"),FileAllowed(['mp4','avi'],message='只能上传mp4和avi')],
                    description="文件",render_kw={"id": "input_url"})
    info = TextAreaField(label="简介",validators=[DataRequired("请输入简介！")],description="简介",
                         render_kw={"class": "form-control","rows": 10,"id": "input_info"})
    logo = FileField(label="封面",validators=[DataRequired("请上传封面！")],description="封面",
                     render_kw={"id": "input_logo"})
    star = SelectField(label="星级",validators=[DataRequired("请选择星级！")],
                       coerce=int,choices=[(0, "未选择"), (1, "1星"), (2, "2星"), (3, "3星"), (4, "4星"), (5, "5星")],
                       description="星级",render_kw={ "class": "form-control","id": "input_star"})
    tag_id = SelectField(label="标签",validators=[DataRequired("请选择标签！")],
                         coerce=int,choices='',
                         description="标签",render_kw={ "class": "form-control","id": "input_tag_id"})
    area = StringField(label="地区",validators=[DataRequired("请输入地区！")],description="地区",
                       render_kw={"class": "form-control","id": "input_area","placeholder": "请输入地区！"})
    length = StringField(label="片长",validators=[DataRequired("请输入片长！")],description="片长",
                         render_kw={"class": "form-control","id": "input_length","placeholder": "请输入片长！"})
    release_time = StringField(label="上映时间",validators=[DataRequired("请选择上映时间！")],description="上映时间",
                               render_kw={"class": "form-control","id":\
                                   "input_release_time","placeholder": "请选择上映时间！"})
    submit = SubmitField('提交',render_kw={"class": "btn btn-primary"})

class PreviewForm(FlaskForm):
    """预告表单"""
    title = StringField(label="预告标题",validators=[DataRequired("请输入预告标题！")],
                        description="预告标题",
                        render_kw={"class": "form-control","id": "input_title","autofocus": "",
                                   "placeholder": "请输入预告标题！"})
    logo = FileField(label="预告封面",validators=[DataRequired("请上传预告封面！"),FileAllowed(['png','jpg','gif'])],
                     description="预告封面",render_kw={"id": "input_logo"})
    submit = SubmitField('提交',render_kw={"class": "btn btn-primary"})

class PwdForm(FlaskForm):
    """修改密码"""
    old_pwd = PasswordField(label="旧密码",validators=[DataRequired("请输入旧密码！")],description="旧密码",
                            render_kw={"class": "form-control","autofocus": "","placeholder": "请输入旧密码！"})
    new_pwd = PasswordField(label="新密码",validators=[DataRequired("请输入新密码！") ],description="新密码",
                            render_kw={"class": "form-control","placeholder": "请输入新密码！"})
    submit = SubmitField('提交',render_kw={"class": "btn btn-primary"})


class AuthForm(FlaskForm):
    """权限表单"""
    name = StringField(label="权限名称",validators=[DataRequired("请输入权限名称！")],
                       description="权限名称",
                       render_kw={"class": "form-control","id": "input_name",
                                  "autofocus": "","placeholder": "请输入权限名称！"})
    url = StringField(label="权限地址",validators=[DataRequired("请输入权限地址！")],
                      description="权限地址",
                      render_kw={"class": "form-control","id": "input_url","placeholder": "请输入权限地址！"})
    submit = SubmitField('提交',render_kw={"class": "btn btn-primary"})


    def validate_name(self, field):
        auth = Auth.query.filter_by(name=field.data).count()
        if auth == 1:
            raise ValidationError("名称已经存在！")

    def validate_url(self, field):
        auth = Auth.query.filter_by(url=field.data).count()
        if auth == 1:
            raise ValidationError("地址已经存在！")


class RoleForm(FlaskForm):
    """角色表单"""
    name = StringField(label="角色名称",validators=[DataRequired("请输入角色名称！")],
                       description="角色名称",
                       render_kw={"class": "form-control","id": "input_name",
                                  "autofocus": "","placeholder": "请输入角色名称！"})
    auths = SelectMultipleField(label="权限列表",validators=[DataRequired("请选择操作权限！")],
                                coerce=int,choices='',
                                description="权限列表",render_kw={"class": "form-control"})
    submit = SubmitField('提交',render_kw={"class": "btn btn-primary"})

    def validate_name(self, field):
        if Role.query.filter_by(name=field.data).count() == 1:
            from app.admin.views import edit_role_name
            if edit_role_name != field.data:
                raise ValidationError("名称已经存在！")


class AdminForm(FlaskForm):
    """管理员表单"""
    name = StringField(label="管理员名称",validators=[DataRequired("请输入管理员名称！")],
        description="管理员名称",
        render_kw={ "class": "form-control","autofocus": "","placeholder": "请输入账号！"})
    pwd = PasswordField(label="管理员密码",validators=[DataRequired("请输入管理员密码！")],description="管理员密码",
                        render_kw={"class": "form-control","placeholder": "请输入管理员密码！"})
    re_pwd = PasswordField(label="管理员重复密码",
                           validators=[DataRequired("请再次输入管理员密码！"),EqualTo('pwd', message="两次密码输入不一致！")],
                           description="管理员重复密码",
                           render_kw={"class": "form-control","placeholder": "请再次输入管理员密码！"})
    role_id = SelectField(label="所属角色",validators=[DataRequired("请选择所属角色！")],
                          coerce=int,
                          choices='',
                          description="所属角色",
                          render_kw={"class": "form-control","id": "input_role_id"})
    submit = SubmitField('提交',render_kw={"class": "btn btn-primary"})

    def validate_name(self, field):
        auth = Admin.query.filter_by(name=field.data).count()
        if auth == 1:
            raise ValidationError("管理员名称已经存在！")
