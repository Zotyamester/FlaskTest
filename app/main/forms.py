from app.models import User
from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=1, max=64)])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=256)])
    submit = SubmitField('Save changes')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Username is unavailable.')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[
                        DataRequired(), Length(min=1, max=128)])
    post = TextAreaField('Body', validators=[
                         DataRequired(), Length(min=0, max=2048)])
    submit = SubmitField('Post')


class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[
                            DataRequired(), Length(min=1, max=512)])
    submit = SubmitField('Send')
