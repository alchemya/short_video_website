from app import create_app
import app.models
from flask_script import Manager
from flask_migrate import MigrateCommand,Migrate
from app.exts import db

app=create_app()
manage=Manager(app)
Migrate(app,db)
manage.add_command('db',MigrateCommand)


if __name__ == '__main__':
    manage.run()