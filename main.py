import os
from secrets import token_bytes
from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm

print(os.environ)

app = Flask(__name__)
app.config['SECRET_KEY'] = token_bytes()
app.config['SQLALCHEMY_ECHO'] = True
ckeditor = CKEditor(app)
Bootstrap5(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro')

login_manager = LoginManager()
login_manager.init_app(app)


def admin_only(function):
    @wraps(function)
    def decorated_view(*args, **kwargs):
        if current_user.is_anonymous or current_user.id != 1:
            return abort(code=403)
        else:
            return function(*args, **kwargs)
    return decorated_view


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

# CONNECT TO DB
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///posts.db"
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    author = relationship("User", back_populates="posts")
    post_comments = relationship("Comment", back_populates="parent_post")

    __tablename__ = "blog_post"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class User(db.Model, UserMixin):
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password_hash = db.Column(db.String, nullable=False)


class Comment(db.Model):
    author = relationship("User", back_populates="comments")
    parent_post = relationship("BlogPost", back_populates="post_comments")

    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    parent_post_id = db.Column(db.Integer, db.ForeignKey("blog_post.id"))
    text = db.Column(db.String, nullable=False)


with app.app_context():
    db.create_all()



@app.route('/register', methods=["GET", "POST"])
def register():
    reg_form = RegisterForm()
    if reg_form.validate_on_submit():
        new_user = User(
            name=reg_form.name.data,
            email=reg_form.email.data,
            password_hash=generate_password_hash(reg_form.password.data, salt_length=8)
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account is already associated with that email!")
            return redirect(url_for('login'))
        else:
            flash("Account created. Welcome!")
            login_user(user=new_user)
            return redirect(url_for('get_all_posts'))

    return render_template("register.html", reg_form=reg_form)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == login_form.email.data)).scalar()
        if not user:
            flash("No account found for that email address!")
        elif not check_password_hash(user.password_hash, login_form.password.data):
            flash("Incorrect password!")
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    comments = db.session.execute(db.select(Comment).where(Comment.parent_post_id == requested_post.id)).scalars()
    if comment_form.validate_on_submit():
        if current_user.is_anonymous:
            flash("You must log in to post comments.")
            return redirect(url_for('login'))
        comment_text = comment_form.body.data
        new_comment = Comment(
            author=current_user,
            parent_post=requested_post,
            author_id=current_user.id,
            text=comment_text,
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template("post.html", post=requested_post, comment=comment_form, comments=comments)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=False, port=5002)
