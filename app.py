from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

# Секретный ключ для работы сессиями
app.secret_key = 'your_secret_key'

# Настроим Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Простая база данных в памяти для пользователей и заявок
users_db = {}
tickets_db = []
user_counter = 1  # Для создания уникальных ID пользователей
ticket_counter = 1  # Для создания уникальных ID заявок

# Модель пользователя
class User(UserMixin):
    def __init__(self, id, username, password, role='user'):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

# Модель заявки
class Ticket:
    def __init__(self, id, user_id, title, description, status='new'):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.status = status

# Загрузка пользователя по id
@login_manager.user_loader
def load_user(user_id):
    return users_db.get(int(user_id))

# Главная страница
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    global user_counter
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users_db:
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('register'))
        
        user = User(id=user_counter, username=username, password=password)
        users_db[user_counter] = user
        user_counter += 1
        
        flash('Вы успешно зарегистрированы!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Страница логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = next((u for u in users_db.values() if u.username == username), None)

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))

        flash('Неверные данные для входа', 'danger')
    return render_template('login.html')

# Страница выхода
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# Страница создания заявки
@app.route('/tickets/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    global ticket_counter
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ticket = Ticket(id=ticket_counter, user_id=current_user.id, title=title, description=description)
        tickets_db.append(ticket)
        ticket_counter += 1
        flash('Заявка успешно создана', 'success')
        return redirect(url_for('view_tickets'))

    return render_template('new_ticket.html')

# Страница просмотра всех заявок (для админа) или только своих (для пользователя)
@app.route('/tickets')
@login_required
def view_tickets():
    if current_user.role == 'admin':
        tickets = tickets_db
    else:
        tickets = [ticket for ticket in tickets_db if ticket.user_id == current_user.id]
    return render_template('view_tickets.html', tickets=tickets)

# Страница просмотра одной заявки
@app.route('/tickets/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = next((t for t in tickets_db if t.id == ticket_id), None)
    if ticket is None:
        flash('Заявка не найдена', 'danger')
        return redirect(url_for('view_tickets'))

    if ticket.user_id != current_user.id and current_user.role != 'admin':
        flash('Вы не имеете доступа к этой заявке', 'danger')
        return redirect(url_for('view_tickets'))

    return render_template('view_ticket.html', ticket=ticket)

# Страница обновления заявки
@app.route('/tickets/<int:ticket_id>/update', methods=['GET', 'POST'])
@login_required
def update_ticket(ticket_id):
    ticket = next((t for t in tickets_db if t.id == ticket_id), None)
    if ticket is None:
        flash('Заявка не найдена', 'danger')
        return redirect(url_for('view_tickets'))

    if ticket.user_id != current_user.id and current_user.role != 'admin':
        flash('Вы не имеете доступа к этой заявке', 'danger')
        return redirect(url_for('view_tickets'))

    if request.method == 'POST':
        ticket.title = request.form['title']
        ticket.description = request.form['description']
        ticket.status = request.form['status']
        flash('Заявка успешно обновлена', 'success')
        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    return render_template('update_ticket.html', ticket=ticket)

# Страница удаления заявки
@app.route('/tickets/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    ticket = next((t for t in tickets_db if t.id == ticket_id), None)
    if ticket is None:
        flash('Заявка не найдена', 'danger')
        return redirect(url_for('view_tickets'))
    
    if ticket.user_id != current_user.id and current_user.role != 'admin':
        flash('Вы не имеете доступа к этой заявке', 'danger')
        return redirect(url_for('view_tickets'))

    tickets_db.remove(ticket)
    flash('Заявка успешно удалена', 'success')
    return redirect(url_for('view_tickets'))

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)

