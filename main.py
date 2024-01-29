
# Import necessary modules
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user

# Create a Flask application instance
app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Define the User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

# Define the Document model
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    collaborators = db.relationship('User', secondary='document_collaborators')

# Define the DocumentCollaborators model
class DocumentCollaborators(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Initialize the database
db.init_app(app)

# Configure the Flask-Login extension
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define the login function
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

# Define the logout function
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Define the home page route
@app.route('/')
def index():
    if current_user.is_authenticated:
        documents = Document.query.filter_by(user_id=current_user.id).all()
        return render_template('index.html', documents=documents)
    else:
        return redirect(url_for('login'))

# Define the route for creating a new document
@app.route('/documents/create', methods=['GET', 'POST'])
def create_document():
    if current_user.is_authenticated:
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            document = Document(title=title, content=content, user_id=current_user.id)
            db.session.add(document)
            db.session.commit()
            return redirect(url_for('index'))
        return render_template('create_document.html')
    else:
        return redirect(url_for('login'))

# Define the route for editing a document
@app.route('/documents/<int:id>/edit', methods=['GET', 'POST'])
def edit_document(id):
    if current_user.is_authenticated:
        document = Document.query.get_or_404(id)
        if document.user_id == current_user.id:
            if request.method == 'POST':
                document.title = request.form['title']
                document.content = request.form['content']
                db.session.commit()
                return redirect(url_for('index'))
            return render_template('edit_document.html', document=document)
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

# Define the route for sharing a document
@app.route('/documents/<int:id>/share', methods=['GET', 'POST'])
def share_document(id):
    if current_user.is_authenticated:
        document = Document.query.get_or_404(id)
        if document.user_id == current_user.id:
            if request.method == 'POST':
                username = request.form['username']
                user = User.query.filter_by(username=username).first()
                if user:
                    document_collaborator = DocumentCollaborators(document_id=document.id, user_id=user.id)
                    db.session.add(document_collaborator)
                    db.session.commit()
                return redirect(url_for('index'))
            return render_template('share_document.html', document=document)
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

# Define the route for viewing a document
@app.route('/documents/<int:id>')
def view_document(id):
    if current_user.is_authenticated:
        document = Document.query.get_or_404(id)
        if document.user_id == current_user.id or document in current_user.collaborators:
            return render_template('view_document.html', document=document)
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

# Define the route for the profile page
@app.route('/profile')
def profile():
    if current_user.is_authenticated:
        return render_template('profile.html', user=current_user)
    else:
        return redirect(url_for('login'))

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
