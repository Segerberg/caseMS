from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('cases.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Kontrollera dina inloggningsuppgifter och försök igen.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('cases.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


# Create initial admin user if needed
@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    # Check if any users exist
    if User.query.count() > 0:
        flash('Systemet är redan konfigurerat.', 'info')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Administratörskonto har skapats!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/setup.html')