from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Создание класса User для работы с Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

    def get_id(self):
        return str(self.id)

# Список пользователей (для примера)
users = [
    User(id=1, username='user1', password='password1', role='user'),
    User(id=2, username='admin', password='adminpass', role='admin')
]

# Список заявок (для примера)
tickets = [
    {'id': 1, 'title': 'Не работает интернет', 'description': 'Скорость ниже заявленной.', 'status': 'open', 'author': 'user1'},
    {'id': 2, 'title': 'Проблема с компьютером', 'description': 'Не включается ноутбук.', 'status': 'in progress', 'author': 'user2'},
]

# Загрузка пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return next((user for user in users if user.id == int(user_id)), None)

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = next((user for user in users if user.username == username), None)
        
        if user and user.password == password:
            login_user(user)  # Авторизация
            return redirect(url_for('index'))  # Перенаправление на главную страницу
        else:
            flash('Неверный логин или пароль')
    
    return render_template('login.html')

# Страница выхода
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Главная страница
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html')  # Если авторизован, переходим на страницу заявок
    return redirect(url_for('login'))  # Иначе на страницу входа

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Проверка, существует ли уже пользователь с таким именем
        if any(user.username == username for user in users):
            flash('Пользователь с таким именем уже существует.')
            return redirect(url_for('register'))
        
        # Создание нового пользователя
        new_user = User(
            id=len(users) + 1,  # Новый id
            username=username,
            password=password,  # Хранение пароля в открытом виде (не рекомендуется)
            role='user'  # Новый пользователь не является администратором, роль "user"
        )
        users.append(new_user)
        flash('Регистрация прошла успешно! Теперь вы можете войти.')
        return redirect(url_for('login'))  # Перенаправляем на страницу входа
    
    return render_template('register.html')

# Страница просмотра заявок
@app.route('/tickets')
@login_required
def view_tickets():
    if current_user.role == 'admin':
        return render_template('view_tickets.html', tickets=tickets)
    
    user_tickets = [ticket for ticket in tickets if ticket['author'] == current_user.username]
    return render_template('view_tickets.html', tickets=user_tickets)

# Страница просмотра конкретной заявки
@app.route('/tickets/<int:ticket_id>', methods=['GET'])
@login_required
def view_ticket(ticket_id):
    # Ищем заявку по ID
    ticket = next((ticket for ticket in tickets if ticket['id'] == ticket_id), None)
    
    if ticket is None:
        flash('Заявка не найдена.')
        return redirect(url_for('view_tickets'))

    # Проверяем, имеет ли текущий пользователь право просматривать заявку
    if ticket['author'] != current_user.username and current_user.role != 'admin':
        flash('У вас нет прав для просмотра этой заявки.')
        return redirect(url_for('view_tickets'))
    
    return render_template('view_ticket.html', ticket=ticket)

# Страница создания заявки
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
        flash('Заявка успешно создана!')
        return redirect(url_for('view_tickets'))
    
    return render_template('create_ticket.html')

# Страница редактирования заявки
@app.route('/tickets/edit/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def update_ticket(ticket_id):
    ticket = next((ticket for ticket in tickets if ticket['id'] == ticket_id), None)
    if not ticket:
        flash('Заявка не найдена')
        return redirect(url_for('view_tickets'))

    # Только пользователь, который создал заявку, или администратор может редактировать
    if ticket['author'] != current_user.username and current_user.role != 'admin':
        flash('У вас нет прав для редактирования этой заявки')
        return redirect(url_for('view_tickets'))

    if request.method == 'POST':
        ticket['title'] = request.form['title']
        ticket['description'] = request.form['description']
        ticket['status'] = request.form['status']
        flash('Заявка обновлена')
        return redirect(url_for('view_tickets'))
    
    return render_template('update_ticket.html', ticket=ticket)

# Страница удаления заявки
@app.route('/tickets/delete/<int:ticket_id>', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    ticket = next((ticket for ticket in tickets if ticket['id'] == ticket_id), None)
    if not ticket:
        flash('Заявка не найдена')
        return redirect(url_for('view_tickets'))

    # Только пользователь, который создал заявку, или администратор может удалить
    if ticket['author'] != current_user.username and current_user.role != 'admin':
        flash('У вас нет прав для удаления этой заявки')
        return redirect(url_for('view_tickets'))

    tickets.remove(ticket)
    flash('Заявка удалена')
    return redirect(url_for('view_tickets'))

if __name__ == '__main__':
    app.run(debug=True)


