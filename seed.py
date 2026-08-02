from productivity_app import create_app, db
from productivity_app.models import User, Note

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    alice = User(username="alice")
    alice.set_password("secret123")
    bob = User(username="bob")
    bob.set_password("secret123")

    db.session.add_all([alice, bob])
    db.session.commit()

    notes = [
        Note(title="Plan the week", content="Review sprint goals", category="work", user_id=alice.id),
        Note(title="Mood check", content="Feeling focused", category="personal", user_id=alice.id),
        Note(title="Gym routine", content="Pushups and stretches", category="fitness", user_id=bob.id),
    ]
    db.session.add_all(notes)
    db.session.commit()
    print("Seed data created")
