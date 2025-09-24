from pathlib import Path
from sqlalchemy.orm import  sessionmaker
from sqlalchemy import delete, select, update , create_engine
from bot.db.models import ViolationModel, FileModel, ViolationFile
from PIL import Image
import hashlib
import os
import shutil
from pathlib import Path

from bot.utils.image_utils import get_image_aspect_ratio

DATABASE_URL = "sqlite:///otbot.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

session.execute(delete(FileModel))
session.execute(delete(ViolationFile))
session.commit()

BASEDIR = Path("images")
for i in BASEDIR.rglob("*.jpg"):
    with open(i, "rb") as img:
        aspect_ratio = get_image_aspect_ratio(img.read())
    session.add(FileModel(hash=i.stem, path=str(i), aspect_ratio=aspect_ratio ))
session.commit()

viols = session.execute(select(ViolationModel)).scalars().all()

for i in viols:
    session.add(ViolationFile(violation_id=i.id, file_hash=i.picture_hash))
session.commit()

