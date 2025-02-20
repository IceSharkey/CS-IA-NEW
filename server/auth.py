from flask import Blueprint, request, jsonify, redirect, url_for, render_template
from flask_login import login_user, login_required, logout_user, current_user
from google.oauth2 import id_token
from google.auth.transport import requests as google_auth_requests
import os
from .models import db, User, Role, UserRoles

auth = Blueprint("auth", __name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        try:
            token = request.json.get("credential")
            if not token:
                return (
                    jsonify({"success": False, "message": "No credential provided"}),
                    400,
                )

            idinfo = id_token.verify_oauth2_token(
                token, google_auth_requests.Request(), GOOGLE_CLIENT_ID
            )

            user = User.query.filter_by(id=idinfo["sub"]).first()
            if not user:
                user = User(
                    id=idinfo["sub"], name=idinfo["name"], email=idinfo["email"]
                )
                db.session.add(user)
                db.session.commit()
            
            
            if user.email == "s1401005@elearn.logosacademy.edu.hk":
                if not user.roles:
                    role = Role.query.filter_by(name="Administrator").first()
                    user_role = UserRoles(user_id=user.id, role_id=role.id)
                    db.session.add(user_role)
                    db.session.commit()

            if not user.roles:
                role = Role.query.filter_by(name="Waitlist").first()
                user_role = UserRoles(user_id=user.id, role_id=role.id)
                db.session.add(user_role)
                db.session.commit()


            login_user(user)
            return jsonify({"success": True})
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 401
        except Exception as e:
            return jsonify({"success": False, "message": "An error occurred"}), 500


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
