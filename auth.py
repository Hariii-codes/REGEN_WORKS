"""
Authentication routes and forms for the ReGenWorks application.
"""

import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app import db, bcrypt
from models import User

logger = logging.getLogger(__name__)

# Create the auth blueprint
auth_bp = Blueprint('auth', __name__)

# Define the forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=20)
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')
    ])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        try:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username is already taken. Please choose a different one.')
        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Error validating username: {str(e)}", exc_info=True)
            # Don't raise validation error here - let the form handle it
            # This prevents masking database errors
            pass
            
    def validate_email(self, email):
        try:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email is already registered. Please use a different one.')
        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Error validating email: {str(e)}", exc_info=True)
            # Don't raise validation error here - let the form handle it
            # This prevents masking database errors
            pass

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

# Define the routes
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Check if database tables exist - use a simpler check
            try:
                # Just check if we can access the database, don't query for users
                # This avoids issues with empty tables or connection problems
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                tables_lower = [t.lower() for t in tables]
                
                if 'user' not in tables_lower:
                    logger.error("User table does not exist in database")
                    flash('Database is not initialized. Please contact the administrator.', 'danger')
                    return render_template('register.html', title='Register', form=form)
                    
            except SQLAlchemyError as e:
                logger.error(f"Database connection error: {str(e)}")
                flash('Database connection error. Please try again later.', 'danger')
                return render_template('register.html', title='Register', form=form)
            except Exception as e:
                logger.error(f"Error checking database: {str(e)}", exc_info=True)
                # Don't block registration if we can't check - try to proceed
                logger.warning("Proceeding with registration despite check failure")
            
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"User registered successfully: {user.username} ({user.email})")
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Integrity error during registration: {str(e)}")
            # Check if it's a duplicate username or email
            if 'username' in str(e).lower() or 'unique constraint' in str(e).lower():
                flash('Username or email already exists. Please choose different credentials.', 'danger')
            else:
                flash('An error occurred during registration. Please try again.', 'danger')
                
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error during registration: {str(e)}")
            flash('A database error occurred. Please try again later.', 'danger')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
            flash('An unexpected error occurred. Please try again later.', 'danger')
    
    # Log form validation errors
    if form.errors:
        logger.warning(f"Form validation errors: {form.errors}")
    
    return render_template('register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    from rewards import get_user_stats
    
    # Get user stats for display
    stats = get_user_stats(current_user.id)
    
    return render_template('profile.html', title='Profile', stats=stats)