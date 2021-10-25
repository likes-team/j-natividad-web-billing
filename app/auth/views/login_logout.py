from werkzeug.urls import url_parse
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_user, logout_user, login_required
from app import mongo
from app.auth import bp_auth
from app.auth.models import User
from app.auth.forms import LoginForm
from app.admin import admin_urls
from app.auth import auth_urls
from app.auth import auth_templates
from app.auth.permissions import load_permissions



@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for(admin_urls['admin']))
        return render_template(auth_templates['login'], \
            title=current_app.config['ADMIN']['APPLICATION_NAME'], form=form)
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for(current_app.config['AUTH']['LOGIN_REDIRECT_URL']))

    user = User.find_one_by_username(form.username.data)

    if not user:
        flash('Invalid username or password','error')
        return redirect(url_for(auth_urls['login']))

    if not user.active:
        flash('Your account is not approved yet!, please contact system administrator','error')
        return redirect(url_for(auth_urls['login']))

    if user is None or not user.check_password(form.password.data):
        flash('Invalid username or password','error')
        return redirect(url_for(auth_urls['login']))

    login_user(user, remember=form.remember_me.data)
    
    load_permissions(user.id)
    
    next_page = request.args.get('next')
    
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for(current_app.config['AUTH']['LOGIN_REDIRECT_URL'])
    
    return redirect(next_page)


@bp_auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('core.index'))
