from datetime import datetime

from app import db
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, MessageForm, PostForm
from app.models import Message, Notification, Post, User
from flask import (current_app, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


def order_and_paginate_posts(posts, page):
    return posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)


def posts_to_json(posts):
    return jsonify({
        'posts': [
            {
                'title': post.title,
                'author': post.author.username,
                'body': post.body
            } for post in posts.items]
    })


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    if current_user.is_anonymous:
        return redirect(url_for('main.explore'))
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,
                    body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.index'))
    posts = current_user.followed_posts().paginate(
        1, current_app.config['POSTS_PER_PAGE'], False)
    return render_template('index.html', title='Home', form=form, posts=posts.items)


@bp.route('/posts', methods=['GET', 'POST'])
@bp.route('/index/posts', methods=['GET', 'POST'])
def index_posts():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts()
    return posts_to_json(order_and_paginate_posts(posts, page))


@bp.route('/explore')
def explore():
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        1, current_app.config['POSTS_PER_PAGE'], False)
    return render_template('index.html', title='Explore', posts=posts.items)


@bp.route('/explore/posts')
def explore_posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query
    return posts_to_json(order_and_paginate_posts(posts, page))


@bp.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        1, current_app.config['POSTS_PER_PAGE'], False)
    form = EmptyForm()
    return render_template('user.html', title=user.username, user=user, posts=posts.items, form=form)


@bp.route('/user/<username>/posts')
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts
    return posts_to_json(order_and_paginate_posts(posts, page))


@bp.route('/user/<username>/popup')
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('_user.html', user=user, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    elif form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('main.user', username=username))
    return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('Your are not following {}'.format(username))
        return redirect(url_for('main.user', username=username))
    return redirect(url_for('main.index'))


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title='Send message', form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for(
        'main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for(
        'main.messages', page=messages.prev_num) if messages.has_prev else None
    return render_template('messages.html', messages=messages.items, next_url=next_url, prev_url=prev_url)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.desc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
