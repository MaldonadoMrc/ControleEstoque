from app import create_app
from app import db
from app.models import db
app = create_app()



def init_db():
    db.init_app(app)
    db.app = app
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)