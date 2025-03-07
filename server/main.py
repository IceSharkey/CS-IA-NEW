from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from .forms import KeywordSearchForm
from functools import wraps
from .models import Transcription, TranscriptionSegment
from sqlalchemy import func
import re
import os
from .models import db, UserRoles, Role, User

main = Blueprint("main", __name__)


# this template filter is to highlight keywords in the text
@main.app_template_filter("highlight_keyword")
def highlight_keyword(text, keyword):
    if not keyword:
        return text
    pattern = re.compile(f"({re.escape(keyword)})", re.IGNORECASE)
    return pattern.sub(r"<mark>\1</mark>", text)


@main.route("/")
def index():
    if current_user.is_authenticated:
            return redirect(url_for("main.home"))
    return render_template("login.html")

def roles_accepted(*role_names):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            for role_name in role_names:
                role = Role.query.filter_by(name=role_name).first()
                if role and UserRoles.query.filter_by(user_id=current_user.id, role_id=role.id).first():
                    return func(*args, **kwargs)
            return redirect(url_for("main.waitlist"))
        return decorated_function
    return decorator

def roles_required(*role_names):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            for role_name in role_names:
                role = Role.query.filter_by(name=role_name).first()
                if role and UserRoles.query.filter_by(user_id=current_user.id, role_id=role.id).first():
                    return func(*args, **kwargs)
            return redirect(url_for("main.home"))
        return decorated_function
    return decorator

@main.route("/home")
@login_required
@roles_accepted('Administrator', 'Moderator', 'User')
def home():
    return render_template("base.html")


@main.route("/home/report", methods=["GET", "POST"])
@login_required
@roles_accepted('Administrator', 'Moderator', 'User')
def report():
    form = KeywordSearchForm()
    results = None
    total_occurrences = 0
    total_files = 0
    percentage = 0
    count = 0
    if form.validate_on_submit():
        keyword = form.keyword.data.lower()

        # Get total number of transcriptions for the user
        total_files = Transcription.query.filter_by(user_id=current_user.id).count()

        # Query for transcriptions containing the keyword
        transcriptions = (
            Transcription.query.join(TranscriptionSegment)
            .filter(
                Transcription.user_id == current_user.id,
                func.lower(TranscriptionSegment.text).like(f"%{keyword}%"),
            )
            .all()
        )

        results = []
        for trans in transcriptions:
            count = sum(
                segment.text.lower().count(keyword) for segment in trans.segments
            )
            if count > 0:
                total_occurrences += count
                results.append(
                    {
                        "filename": trans.filename,
                        "count": count,
                        "segments": [
                            {
                                "timestamp": f"{seg.start_time} - {seg.end_time}",
                                "text": seg.text,
                            }
                            for seg in trans.segments
                            if keyword.lower() in seg.text.lower()
                        ],
                    }
                )

        # Calculate percentage of files containing the keyword
        percentage = round((len(results) / total_files * 100) if total_files > 0 else 0)
        count = len(results)

    return render_template(
        "report.html",
        form=form,
        results=results,
        count=count,
        keyword=form.keyword.data if form.validate_on_submit() else "",
        total_occurrences=total_occurrences,
        total_files=total_files,
        percentage=percentage,
    )


@main.route("/home/manage", methods=["GET", "POST"])
@login_required
@roles_required('Administrator', 'Moderator')
def manage():
    waitlist_users = User.query.join(UserRoles).join(Role).filter(Role.id == 4).all()
    all_users = User.query.join(UserRoles).join(Role).filter(Role.id == 3).all()
    moderators = User.query.join(UserRoles).join(Role).filter(Role.id == 2).all()
    current_user_role = UserRoles.query.filter_by(user_id=current_user.id).first().role_id
    return render_template("manage.html", waitlist_users=waitlist_users, all_users=all_users, moderators=moderators, current_user_role=current_user_role)

@main.route("/home/manage/update-role", methods=["POST"])
@login_required
@roles_accepted('Administrator', 'Moderator')
def update_role():
    user_id = request.form.get("user_id")
    user_role = UserRoles.query.filter_by(user_id=user_id).first()
    if user_role:
        user_role.role_id = 3
        db.session.commit()
        return jsonify({"message": "Role updated successfully"})
    else:
        return jsonify({"message": "User not found"}), 404
    
@main.route("/home/manage/promote-moderator", methods=["POST"])
@login_required
@roles_accepted('Administrator')
def promote_role():
    user_id = request.form.get("user_id")
    user_role = UserRoles.query.filter_by(user_id=user_id).first()
    if user_role:
        user_role.role_id = 2
        db.session.commit()
        return jsonify({"message": "Role updated successfully"})
    else:
        return jsonify({"message": "User not found"}), 404
    
@main.route("/home/manage/delete-role", methods=["POST"])
@login_required
@roles_accepted('Administrator', 'Moderator')
def delete_user_role():
    user_id = request.form.get("user_id")
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"})
    else:
        return jsonify({"message": "User not found"}), 404


@main.route("/home/records")
@login_required
@roles_accepted('Administrator', 'Moderator', 'User')
def records():
    transcriptions = (
        Transcription.query.filter_by(user_id=current_user.id)
        .order_by(Transcription.upload_date.desc())
        .all()
    )
    return render_template("records.html", transcriptions=transcriptions)


@main.route("/home/records/delete/<int:id>")
@login_required
@roles_accepted('Administrator', 'Moderator', 'User')
def delete_record(id):
    transcription = Transcription.query.get_or_404(id)
    if transcription.user_id != current_user.id:
        flash("Unauthorized action", "error")
        return redirect(url_for("main.records"))

    # Delete the file
    try:
        if os.path.exists(transcription.file_path):
            os.remove(transcription.file_path)
    except Exception as e:
        flash(f"Warning: Could not delete file: {str(e)}", "error")

    # Delete from database
    try:
        db.session.delete(transcription)  # This will cascade delete segments
        db.session.commit()
        flash("Record deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting record: {str(e)}", "error")

    return redirect(url_for("main.records"))


@main.route("/home/records/view/<int:id>")
@login_required
@roles_accepted('Administrator', 'Moderator', 'User')
def view_record(id):
    transcription = Transcription.query.get_or_404(id)
    if transcription.user_id != current_user.id:
        flash("Unauthorized action", "error")
        return redirect(url_for("main.records"))

    segments = transcription.segments
    return render_template(
        "view_record.html", transcription=transcription, segments=segments
    )

@main.route("/waitlist")
def waitlist():
    return render_template("waitlist.html")