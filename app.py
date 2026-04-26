from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import json
import os
import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
            for i, user in enumerate(users):
                if 'id' not in user:
                    user['id'] = i + 1
                if 'score' not in user:
                    user['score'] = 0
                if 'avatar' not in user:
                    user['avatar'] = None
                if 'grade' not in user:
                    user['grade'] = 'Не указан'
                if 'nickname' not in user:
                    user['nickname'] = 'Аноним'
                if 'completed_tasks' not in user:
                    user['completed_tasks'] = 0
                if 'best_streak' not in user:
                    user['best_streak'] = 0
                if 'current_streak' not in user:
                    user['current_streak'] = 0
                if 'created_at' not in user:
                    user['created_at'] = 'Недавно'
                if 'password' not in user:
                    user['password'] = hash_password('password123')
                if 'settings' not in user:
                    user['settings'] = {'hints': True}
                if 'theme_progress' not in user:
                    themes = ['algorithms', 'logic', 'loops', 'conditions', 'lists', 'storage', 'flowcharts', 'detective', 'mixed']
                    user['theme_progress'] = {}
                    for theme in themes:
                        user['theme_progress'][theme] = {'stars': 0, 'status': 'start'}
                if 'difficulty_progress' not in user:
                    user['difficulty_progress'] = {}
            return users
    return []

def save_users(users):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_questions():
    if os.path.exists('questions.json'):
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form.get('nickname')
        password = request.form.get('password')
        users = load_users()
        for user in users:
            if user.get('nickname') == nickname:
                if user.get('password') == hash_password(password):
                    session['user_id'] = user['id']
                    flash(f'С возвращением, {nickname}!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Неверный пароль!', 'error')
                    return redirect(url_for('login'))
        flash('Пользователь не найден!', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    nickname = request.form.get('nickname')
    password = request.form.get('password')
    grade = request.form.get('grade')
    
    if not nickname or not password or not grade:
        flash('Заполните все поля!', 'error')
        return redirect(url_for('index'))
    if len(password) < 4:
        flash('Пароль должен быть не менее 4 символов!', 'error')
        return redirect(url_for('index'))
    
    users = load_users()
    for user in users:
        if user.get('nickname') == nickname:
            flash('Такой никнейм уже существует!', 'error')
            return redirect(url_for('index'))
    
    max_id = max([u.get('id', 0) for u in users]) if users else 0
    themes = ['algorithms', 'logic', 'loops', 'conditions', 'lists', 'storage', 'flowcharts', 'detective', 'mixed']
    theme_progress = {theme: {'stars': 0, 'status': 'start'} for theme in themes}
    
    new_user = {
        'id': max_id + 1,
        'nickname': nickname,
        'password': hash_password(password),
        'grade': grade,
        'score': 0,
        'avatar': None,
        'completed_tasks': 0,
        'best_streak': 0,
        'current_streak': 0,
        'created_at': datetime.datetime.now().strftime('%d.%m.%Y'),
        'settings': {'hints': True},
        'theme_progress': theme_progress,
        'difficulty_progress': {}
    }
    users.append(new_user)
    save_users(users)
    session['user_id'] = new_user['id']
    return redirect(url_for('choose_avatar'))

@app.route('/choose_avatar')
def choose_avatar():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    users = load_users()
    user = next((u for u in users if u.get('id') == session['user_id']), None)
    if not user:
        return redirect(url_for('index'))
    return render_template('choose_avatar.html', user=user)

@app.route('/save_avatar', methods=['POST'])
def save_avatar():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    avatar = request.form.get('avatar')
    users = load_users()
    for user in users:
        if user.get('id') == session['user_id']:
            user['avatar'] = avatar
            break
    save_users(users)
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    users = load_users()
    user = next((u for u in users if u.get('id') == session['user_id']), None)
    if not user:
        return redirect(url_for('index'))
    open_modal = request.args.get('open_modal')
    return render_template('dashboard.html', user=user, open_modal=open_modal)

@app.route('/game')
def game():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    theme = request.args.get('theme', 'algorithms')
    difficulty = request.args.get('difficulty', 'легкий')
    
    questions = load_questions()
    theme_questions = [q for q in questions if q.get('theme') == theme and q.get('difficulty') == difficulty]
    
    if not theme_questions:
        flash('Вопросы не найдены!', 'error')
        return redirect(url_for('dashboard'))
    
    users = load_users()
    user = None
    for u in users:
        if u.get('id') == session['user_id']:
            user = u
            break
    
    if user is None:
        return redirect(url_for('index'))
    
    progress_key = f'{theme}_{difficulty}'
    if 'difficulty_progress' not in user:
        user['difficulty_progress'] = {}
    if progress_key not in user['difficulty_progress']:
        user['difficulty_progress'][progress_key] = {'current_index': 0, 'completed': [], 'stars': 0}
        save_users(users)
    
    current_index = user['difficulty_progress'][progress_key].get('current_index', 0)
    
    if current_index >= len(theme_questions):
        flash(f'Ты прошел все задания по сложности "{difficulty}"!', 'success')
        return redirect(url_for('dashboard', open_modal=theme))
    
    question = theme_questions[current_index]
    
    theme_names = {
        'algorithms': 'Алгоритмы', 'logic': 'Логика', 'loops': 'Повторители',
        'conditions': 'Выбор и ветвление', 'lists': 'Списки и порядок',
        'storage': 'Хранилища данных', 'flowcharts': 'Блок-схемы',
        'detective': 'Компьютерный детектив', 'mixed': 'Смешанный бой'
    }
    
    return render_template('game.html', 
                         question=question, 
                         theme=theme_names.get(theme, theme),
                         difficulty=difficulty, 
                         current_index=current_index + 1, 
                         total=len(theme_questions),
                         user=user)

@app.route('/check_answer_ajax', methods=['POST'])
def check_answer_ajax():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    answer_raw = request.form.get('answer')
    correct_answer_raw = request.form.get('correct_answer')
    theme = request.form.get('theme')
    difficulty = request.form.get('difficulty')
    question_id = request.form.get('question_id')
    
    theme_keys = {
        'Алгоритмы': 'algorithms', 'Логика': 'logic', 'Повторители': 'loops',
        'Выбор и ветвление': 'conditions', 'Списки и порядок': 'lists',
        'Хранилища данных': 'storage', 'Блок-схемы': 'flowcharts',
        'Компьютерный детектив': 'detective', 'Смешанный бой': 'mixed'
    }
    theme_key = theme_keys.get(theme, theme)
    
    # ========== УНИВЕРСАЛЬНАЯ ПРОВЕРКА ОТВЕТОВ (твоя логика, без изменений) ==========
    is_correct = False
    
    try:
        correct_parsed = json.loads(correct_answer_raw)
        is_multiple = isinstance(correct_parsed, list)
    except (json.JSONDecodeError, TypeError):
        correct_parsed = correct_answer_raw
        is_multiple = False
    
    if is_multiple:
        try:
            user_answers = json.loads(answer_raw) if answer_raw else []
            if not isinstance(user_answers, list):
                user_answers = [answer_raw]
        except (json.JSONDecodeError, TypeError):
            user_answers = [answer_raw] if answer_raw else []
        
        user_set = {str(a).strip().upper() for a in user_answers}
        correct_set = {str(c).strip().upper() for c in correct_parsed}
        is_correct = (user_set == correct_set)
    else:
        user_answer = str(answer_raw).strip().upper() if answer_raw else ""
        correct_answer = str(correct_parsed).strip().upper()
        is_correct = (user_answer == correct_answer)
    # ===================================================
    
    users = load_users()
    user = None
    for u in users:
        if u.get('id') == session['user_id']:
            user = u
            break
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    progress_key = f'{theme_key}_{difficulty}'
    if 'difficulty_progress' not in user:
        user['difficulty_progress'] = {}
    if progress_key not in user['difficulty_progress']:
        user['difficulty_progress'][progress_key] = {'current_index': 0, 'completed': [], 'stars': 0}
    
    current_index = user['difficulty_progress'][progress_key].get('current_index', 0)
    
    if is_correct:
        points = 10
        user['score'] = user.get('score', 0) + points
        user['completed_tasks'] = user.get('completed_tasks', 0) + 1
        user['current_streak'] = user.get('current_streak', 0) + 1
        if user['current_streak'] > user.get('best_streak', 0):
            user['best_streak'] = user['current_streak']
        
        if question_id and question_id not in user['difficulty_progress'][progress_key]['completed']:
            user['difficulty_progress'][progress_key]['completed'].append(question_id)
        
        user['difficulty_progress'][progress_key]['current_index'] = current_index + 1
        
        # ========== НАЧИСЛЕНИЕ ЗВЁЗД ДЛЯ СЛОЖНОСТИ (ИСПРАВЛЕНО) ==========
        # Максимум звёзд для каждой сложности
        if difficulty == 'легкий':
            max_stars = 2
        elif difficulty == 'средний':
            max_stars = 2
        else:  # сложный
            max_stars = 1
        
        total_questions = len([q for q in load_questions() if q.get('theme') == theme_key and q.get('difficulty') == difficulty])
        completed_count = len(user['difficulty_progress'][progress_key]['completed'])
        
        # Звезда даётся только когда пройдены ВСЕ вопросы данной сложности
        if completed_count >= total_questions:
            user['difficulty_progress'][progress_key]['stars'] = max_stars
        else:
            user['difficulty_progress'][progress_key]['stars'] = 0
        
        # ========== ОБНОВЛЕНИЕ ОБЩЕГО ПРОГРЕССА ТЕМЫ (ЗВЁЗДЫ И СТАТУС) ==========
        # Суммируем звёзды по трём сложностям (максимум 5)
        easy_stars = user['difficulty_progress'].get(f'{theme_key}_легкий', {}).get('stars', 0)
        medium_stars = user['difficulty_progress'].get(f'{theme_key}_средний', {}).get('stars', 0)
        hard_stars = user['difficulty_progress'].get(f'{theme_key}_сложный', {}).get('stars', 0)
        total_theme_stars = easy_stars + medium_stars + hard_stars
        
        if 'theme_progress' not in user:
            user['theme_progress'] = {}
        if theme_key not in user['theme_progress']:
            user['theme_progress'][theme_key] = {'stars': 0, 'status': 'start'}
        
        user['theme_progress'][theme_key]['stars'] = total_theme_stars
        
        # Статус темы
        if total_theme_stars == 5:
            user['theme_progress'][theme_key]['status'] = 'completed'
        elif total_theme_stars > 0:
            user['theme_progress'][theme_key]['status'] = 'in_progress'
        else:
            user['theme_progress'][theme_key]['status'] = 'start'
        # ==============================================================
        
        save_users(users)
        message = f'+{points} ⚡'
    else:
        points = 5
        user['score'] = max(0, user.get('score', 0) - points)
        user['current_streak'] = 0
        save_users(users)
        message = f'-{points} ⚡'
    
    # Определяем следующий URL
    theme_questions = [q for q in load_questions() if q.get('theme') == theme_key and q.get('difficulty') == difficulty]
    if user['difficulty_progress'][progress_key]['current_index'] >= len(theme_questions):
        next_url = url_for('dashboard', open_modal=theme_key)
    else:
        next_url = url_for('game', theme=theme_key, difficulty=difficulty)
    
    return jsonify({
        'is_correct': is_correct,
        'points': points,
        'message': message,
        'next_url': next_url
    })

@app.route('/get_theme_progress')
def get_theme_progress():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    theme = request.args.get('theme')
    users = load_users()
    user = None
    for u in users:
        if u.get('id') == session['user_id']:
            user = u
            break
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    easy_key = f'{theme}_легкий'
    medium_key = f'{theme}_средний'
    hard_key = f'{theme}_сложный'
    
    difficulty_progress = user.get('difficulty_progress', {})
    
    easy_stars = difficulty_progress.get(easy_key, {}).get('stars', 0) if easy_key in difficulty_progress else 0
    medium_stars = difficulty_progress.get(medium_key, {}).get('stars', 0) if medium_key in difficulty_progress else 0
    hard_stars = difficulty_progress.get(hard_key, {}).get('stars', 0) if hard_key in difficulty_progress else 0
    
    return jsonify({
        'easy': easy_stars,
        'medium': medium_stars,
        'hard': hard_stars
    })

@app.route('/leaderboard')
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    users = load_users()
    users_sorted = sorted(users, key=lambda x: x.get('score', 0), reverse=True)
    current_user = None
    for u in users:
        if u.get('id') == session['user_id']:
            current_user = u
            break
    return render_template('leaderboard.html', users=users_sorted, current_user=current_user, current_user_id=session['user_id'])

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    users = load_users()
    user = None
    for u in users:
        if u.get('id') == session['user_id']:
            user = u
            break
    if not user:
        return redirect(url_for('index'))
    users_sorted = sorted(users, key=lambda x: x.get('score', 0), reverse=True)
    rank = 1
    for u in users_sorted:
        if u.get('id') == user['id']:
            break
        rank += 1
    user['rank'] = rank
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    new_nickname = request.form.get('nickname')
    new_grade = request.form.get('grade')
    new_avatar = request.form.get('avatar')
    new_password = request.form.get('password')
    users = load_users()
    user = None
    for u in users:
        if u.get('id') == session['user_id']:
            user = u
            break
    if not user:
        return redirect(url_for('index'))
    for u in users:
        if u.get('nickname') == new_nickname and u.get('id') != session['user_id']:
            flash('Этот никнейм уже занят!', 'error')
            return redirect(url_for('profile'))
    user['nickname'] = new_nickname
    user['grade'] = new_grade
    user['avatar'] = new_avatar
    if new_password and len(new_password) >= 4:
        user['password'] = hash_password(new_password)
        flash('Пароль успешно изменен!', 'success')
    save_users(users)
    flash('Профиль успешно обновлен!', 'success')
    return redirect(url_for('profile'))

@app.route('/save_settings', methods=['POST'])
def save_settings():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    settings = request.get_json()
    users = load_users()
    for user in users:
        if user.get('id') == session['user_id']:
            if 'settings' not in user:
                user['settings'] = {}
            if 'hints' in settings:
                user['settings']['hints'] = settings.get('hints', True)
            break
    save_users(users)
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)