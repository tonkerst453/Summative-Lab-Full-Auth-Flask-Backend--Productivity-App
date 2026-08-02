from productivity_app import create_app, db
from productivity_app.models import Note, User

__all__ = ["create_app", "db", "User", "Note"]


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
