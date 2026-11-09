from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User

bp = Blueprint('main', __name__)


# ============ ROUTES CRUD ============

@bp.route('/')
def index():
    users = User.query.order_by(User.date_creation.desc()).all()
    return render_template('index.html', users=users)


@bp.route('/view/<int:id>')
def view(id):
    user = User.query.get_or_404(id)
    return render_template('view.html', user=user)


@bp.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form.get('telephone', '')

        if User.query.filter_by(email=email).first():
            flash('Cet email existe déjà !', 'error')
            return redirect(url_for('main.create'))

        new_user = User(nom=nom, prenom=prenom, email=email, telephone=telephone)
        db.session.add(new_user)
        db.session.commit()

        flash('Utilisateur créé avec succès !', 'success')
        return redirect(url_for('main.index'))

    return render_template('create.html')


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        email = request.form['email']
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            flash('Cet email existe déjà !', 'error')
            return redirect(url_for('main.edit', id=user.id))

        user.nom = request.form['nom']
        user.prenom = request.form['prenom']
        user.email = email
        user.telephone = request.form.get('telephone', '')

        db.session.commit()
        flash('Utilisateur modifié avec succès !', 'success')
        return redirect(url_for('main.index'))

    return render_template('edit.html', user=user)


@bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()

    flash('Utilisateur supprimé avec succès !', 'success')
    return redirect(url_for('main.index'))