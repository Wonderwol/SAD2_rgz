from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')  # Загрузка из переменной окружения

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

    def get_id(self):
        return str(self.id)


users = [
    User(id=1, username='user1', password='password1', role='user'),
    User(id=2, username='admin', password='adminpass', role='admin')
]


tickets = [
    {'id': 1, 'title': 'Не работает интернет', 'description': 'Скорость ниже заявленной.', 'status': 'open', 'author': 'user1'},
    {'id': 2, 'title': 'Проблема с компьютером', 'description': 'Не включается ноутбук.', 'status': 'in progress', 'author': 'user1'},
]


@login_manager.user_loader
def load_user(user_id):
    return next((user for user in users if user.id == int(user_id)), None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = next((user for user in users if user.username == username), None)

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if any(user.username == username for user in users):
            return redirect(url_for('register'))

        new_user = User(id=len(users) + 1, username=username, password=password, role='user')
        users.append(new_user)
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/tickets')
@login_required
def view_tickets():
    if current_user.role == 'admin':
        return render_template('view_tickets.html', tickets=tickets, current_user=current_user)

    user_tickets = [ticket for ticket in tickets if ticket['author'] == current_user.username]
    return render_template('view_tickets.html', tickets=user_tickets, current_user=current_user)


@app.route('/tickets/<int:ticket_id>', methods=['GET'])
@login_required
def view_ticket(ticket_id):
    ticket = next((ticket for ticket in tickets if ticket['id'] == ticket_id), None)

    if ticket is None:
        return redirect(url_for('view_tickets'))

    if ticket['author'] != current_user.username and current_user.role != 'admin':
        return redirect(url_for('view_tickets'))

    return render_template('view_ticket.html', ticket=ticket, current_user=current_user)


@app.route('/tickets/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        new_ticket = {
            'id': len(tickets) + 1,
            'title': title,
            'description': description,
            'status': 'open',
            'author': current_user.username
        }
        tickets.append(new_ticket)
        return redirect(url_for('view_tickets'))

    return render_template('create_ticket.html', current_user=current_user)


@app.route('/tickets/edit/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def update_ticket(ticket_id):
    ticket = next((ticket for ticket in tickets if ticket['id'] == ticket_id), None)
    if not ticket:
        return redirect(url_for('view_tickets'))

    if ticket['author'] != current_user.username and current_user.role != 'admin':
        return redirect(url_for('view_tickets'))

    if request.method == 'POST':
        ticket['title'] = request.form['title']
        ticket['description'] = request.form['description']

        if current_user.role == 'admin':
            ticket['status'] = request.form['status']

        return redirect(url_for('view_tickets'))

    return render_template('update_ticket.html', ticket=ticket, is_admin=(current_user.role == 'admin'), current_user=current_user)


@app.route('/tickets/delete/<int:ticket_id>', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    ticket = next((ticket for ticket in tickets if ticket['id'] == ticket_id), None)
    if not ticket:
        return redirect(url_for('view_tickets'))

    if ticket['author'] != current_user.username and current_user.role != 'admin':
        return redirect(url_for('view_tickets'))

    tickets.remove(ticket)
    return redirect(url_for('view_tickets'))


@app.route('/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        return redirect(url_for('view_tickets'))

    if request.method == 'POST':
        user_id = int(request.form.get('user_id'))
        new_role = request.form.get('role')

        user = next((user for user in users if user.id == user_id), None)
        if user:
            user.role = new_role

    return render_template('view_users.html', users=users, current_user=current_user)


@app.route('/users/update_role/<int:user_id>', methods=['POST'])
@login_required
def update_user_role(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('manage_users'))

    user = next((user for user in users if user.id == user_id), None)
    if not user:
        return redirect(url_for('manage_users'))

    new_role = request.form.get('role')
    if new_role in ['user', 'admin']:
        user.role = new_role

    return redirect(url_for('manage_users'))
