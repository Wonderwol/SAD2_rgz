from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

# Настройка секретного ключа для сессий
app.secret_key = 'your_secret_key'

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Пример пользователей
users = [
    {'id': 1, 'username': 'admin', 'password': 'adminpass', 'role': 'admin'},
    {'id': 2, 'username': 'user1', 'password': 'user1pass', 'role': 'user'},
    {'id': 3, 'username': 'user2', 'password': 'user2pass', 'role': 'user'},
]

# Пример заявок
tickets = [
    {'id': 1, 'title': 'Не работает интернет', 'description': 'Скорость ниже заявленной.', 'status': 'open', 'author': 'user1'},
    {'id': 2, 'title': 'Проблема с компьютером', 'description': 'Не включается ноутбук.', 'status': 'in progress', 'author': 'user2'},
]

# Пользовательская модель
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    user_data = next((u for u in users if u['id'] == int(user_id)), None)
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['role'])
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html')  # Перенаправление на страницу заявок, если пользователь авторизован
    return redirect(url_for('login'))  # Если не авторизован, перенаправить на страницу входа


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if any(user['username'] == username for user in users):
            flash('Пользователь с таким именем уже существует.')
            return redirect(url_for('register'))
        user_id = len(users) + 1
        users.append({'id': user_id, 'username': username, 'password': password, 'role': 'user'})
        flash('Регистрация прошла успешно. Теперь вы можете войти.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            login_user(User(user['id'], user['username'], user['role']))
            return redirect(url_for('view_tickets'))  # Перенаправление на страницу заявок
        flash('Неверное имя пользователя или пароль.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))  # Перенаправление на страницу входа после выхода


@app.route('/tickets/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ticket = {'id': len(tickets) + 1, 'title': title, 'description': description, 'user_id': current_user.id}
        tickets.append(ticket)
        return redirect(url_for('view_tickets'))
    return render_template('new_ticket.html')


@app.route('/tickets')
@login_required
def view_tickets():
    return render_template('view_tickets.html', tickets=tickets)

@app.route('/tickets/<int:ticket_id>', methods=['GET'])
@login_required
def view_ticket(ticket_id):
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    if not ticket:
        flash('Заявка не найдена.')
        return redirect(url_for('view_tickets'))
    return render_template('view_ticket.html', ticket=ticket)

@app.route('/tickets/<int:ticket_id>/update', methods=['GET', 'POST'])
@login_required
def update_ticket(ticket_id):
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    if not ticket:
        flash('Заявка не найдена.')
        return redirect(url_for('view_tickets'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        status = request.form.get('status')
        if title:
            ticket['title'] = title
        if description:
            ticket['description'] = description
        if status:
            ticket['status'] = status
        flash('Заявка успешно обновлена.')
        return redirect(url_for('view_tickets'))

    return render_template('update_ticket.html', ticket=ticket)

@app.route('/tickets/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    global tickets
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    if not ticket:
        flash('Заявка не найдена.')
        return redirect(url_for('view_tickets'))
    tickets = [t for t in tickets if t['id'] != ticket_id]
    flash('Заявка удалена.')
    return redirect(url_for('view_tickets'))

if __name__ == '__main__':
    app.run(debug=True)

