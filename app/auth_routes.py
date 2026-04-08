"""Authentication routes (login/logout)."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user

from app.auth import User
from app.forms import LoginForm

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page.

    Returns:
        Login form or redirect to home if successful
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.email.data, form.password.data)

        if user:
            login_user(user)
            flash(f"Welcome, {user.name}! You are now logged in.", "success")
            return redirect(url_for("main.index"))
        else:
            flash("Invalid email or password. Please try again.", "error")

    return render_template("login.html", form=form)


@bp.route("/logout")
def logout():
    """Logout page.

    Returns:
        Redirect to home page
    """
    logout_user()
    flash("You have been logged out. See you soon!", "info")
    return redirect(url_for("auth.login"))
