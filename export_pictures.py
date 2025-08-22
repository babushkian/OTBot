from pathlib import Path
from sqlalchemy.orm import  sessionmaker
from sqlalchemy import delete, select, update , create_engine
from bot.db.models import ViolationModel
import hashlib
import os
import shutil

DATABASE_URL = "sqlite:///otbot.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()


def create_img_dir():

    BASEDIR = Path("images")
    if BASEDIR.exists():
        shutil.rmtree(BASEDIR)
    BASEDIR.mkdir()
    result = session.execute(select(ViolationModel)).scalars().all()
    for i in result:
        print(i.id, i.description)
        if i.picture:
            # считаем SHA-256
            picture_hash = hashlib.sha256(i.picture).hexdigest()
            # сохраняем файл (например, как hash.jpg)
            subdir = BASEDIR / picture_hash[:2]
            if not subdir.exists():
                subdir.mkdir()

            filepath =  subdir / f"{picture_hash}.jpg"
            if not filepath.exists():
                with open(filepath, "wb") as f:
                    f.write(i.picture)

            # записываем хэш в БД
            i.picture_hash = picture_hash


    session.commit()





if __name__ =="__main__":
    create_img_dir()