from flask import Flask, jsonify, request, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import validates


db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    @validates("username")
    def validate_username(self, key, value):
        if not value or not value.strip():
            raise ValueError("Username is required")
        return value.strip()

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="notes")


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="dev-secret-key",
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route("/signup", methods=["POST"])
    def signup():
        payload = request.get_json(silent=True) or {}
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 409

        user = User(username=username)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "Username already exists"}), 409

        session["user_id"] = user.id
        return jsonify({"id": user.id, "username": user.username}), 201

    @app.route("/login", methods=["POST"])
    def login():
        payload = request.get_json(silent=True) or {}
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid username or password"}), 401

        session["user_id"] = user.id
        return jsonify({"id": user.id, "username": user.username}), 200

    @app.route("/logout", methods=["POST"])
    def logout():
        session.pop("user_id", None)
        return jsonify({"message": "Logged out"}), 200

    @app.route("/check_session")
    def check_session():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        user = db.session.get(User, user_id)
        if not user:
            session.pop("user_id", None)
            return jsonify({"error": "Not authenticated"}), 401

        return jsonify({"id": user.id, "username": user.username}), 200

    @app.before_request
    def require_auth():
        public_routes = {"/signup", "/login", "/logout"}
        if request.path in public_routes:
            return None
        if request.path == "/check_session":
            return None
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        user = db.session.get(User, user_id)
        if not user:
            session.pop("user_id", None)
            return jsonify({"error": "Authentication required"}), 401

    @app.route("/notes", methods=["GET"])
    def list_notes():
        user_id = session.get("user_id")
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=10, type=int)

        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10

        pagination = (
            Note.query.filter_by(user_id=user_id)
            .order_by(Note.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        notes = [
            {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "category": note.category,
                "user_id": note.user_id,
            }
            for note in pagination.items
        ]
        return jsonify(
            {
                "notes": notes,
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page,
                "total": pagination.total,
            }
        ), 200

    @app.route("/notes", methods=["POST"])
    def create_note():
        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "").strip()
        content = (payload.get("content") or "").strip()
        category = (payload.get("category") or "").strip()

        if not title or not content or not category:
            return jsonify({"error": "Title, content, and category are required"}), 400

        user_id = session.get("user_id")
        note = Note(title=title, content=content, category=category, user_id=user_id)
        db.session.add(note)
        db.session.commit()

        return jsonify(
            {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "category": note.category,
                "user_id": note.user_id,
            }
        ), 201

    @app.route("/notes/<int:note_id>", methods=["GET"])
    def show_note(note_id):
        note = Note.query.get_or_404(note_id)
        if note.user_id != session.get("user_id"):
            return jsonify({"error": "You do not have permission to access this note"}), 403
        return jsonify(
            {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "category": note.category,
                "user_id": note.user_id,
            }
        ), 200

    @app.route("/notes/<int:note_id>", methods=["PATCH"])
    def update_note(note_id):
        note = Note.query.get_or_404(note_id)
        if note.user_id != session.get("user_id"):
            return jsonify({"error": "You do not have permission to edit this note"}), 403

        payload = request.get_json(silent=True) or {}
        if "title" in payload:
            note.title = (payload.get("title") or "").strip()
        if "content" in payload:
            note.content = (payload.get("content") or "").strip()
        if "category" in payload:
            note.category = (payload.get("category") or "").strip()

        if not note.title or not note.content or not note.category:
            return jsonify({"error": "Title, content, and category are required"}), 400

        db.session.commit()
        return jsonify(
            {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "category": note.category,
                "user_id": note.user_id,
            }
        ), 200

    @app.route("/notes/<int:note_id>", methods=["DELETE"])
    def delete_note(note_id):
        note = Note.query.get_or_404(note_id)
        if note.user_id != session.get("user_id"):
            return jsonify({"error": "You do not have permission to delete this note"}), 403

        db.session.delete(note)
        db.session.commit()
        return jsonify({"message": "Note deleted"}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
