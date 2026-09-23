from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service import authenticate_user

auth_bp = Blueprint('auth', __name__)


def _redirect_for_role(user):
    if user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('employee.dashboard'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        user = authenticate_user(username, password)
        if user:
            login_user(user)
            return _redirect_for_role(user)

        flash('اسم المستخدم أو كلمة المرور غلط', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))