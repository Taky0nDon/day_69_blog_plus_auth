#flask #auth #100days
## Admin Required decorator

```python
from functools import wraps
from flask import abort


def admin_only(func):
	@wraps(func)
	def decorated_function(*args, **kwargs):
	# if id is not 1 then return abort() with 403 error
		if current_user.id != 1:
			return abort(403)
		else:
			return func(*args, **kwargs)
	return decorated_function
```

## Creating Relational Databases

* We need to create a relationship beteen the `user` table and the `blog posts` table to link them together. This way, we can see which BlodPosts a User has written. Or see which User is the author of a particular BlogPost
* We can define a relationship between tables using a `ForeignKey` and a `relatonship()` method.
* Create a [`One to Many relationship`](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#one-to-many) between the user table and the blog_post table
* user will be the parent
* blog post will be the child

>A one to many relationship places a foreign key on the child table referencing the parent. [`relationship()`](https://docs.sqlalchemy.org/en/20/orm/relationship_api.html#sqlalchemy.orm.relationship "sqlalchemy.orm.relationship") is then specified on the parent, as referencing a collection of items represented by the child:

```python
class Parent(Base):
    __tablename__ = "parent_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    children: Mapped[List["Child"]] = relationship()


class Child(Base):
    __tablename__ = "child_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parent_table.id"))
```

```Python
class BlogPost(db.Model):  
	__tablename__ = "blog_posts"  
	id = db.Column(db.Integer, primary_key=True)  
	title = db.Column(db.String(250), unique=True, nullable=False)  
	subtitle = db.Column(db.String(250), nullable=False)  
	date = db.Column(db.String(250), nullable=False)  
	body = db.Column(db.Text, nullable=False)  
	img_url = db.Column(db.String(250), nullable=False)  

	author = relationship("User", back_populates="posts")  
	author_id = db.Column(db.Integer, db.ForeignKey("user.id"))  
  
  
class User(db.Model, UserMixin):  
	__tablename__ = "user"  
	id = db.Column(db.Integer, primary_key=True)  
	name = db.Column(db.String, nullable=False)  
	email = db.Column(db.String, nullable=False, unique=True)  
	password_hash = db.Column(db.String, nullable=False)  

	posts = relationship("BlogPost", back_populates="author")
```

## Recreate the database with the old data

