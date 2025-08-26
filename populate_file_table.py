from pathlib import Path
from sqlalchemy.orm import  sessionmaker
from sqlalchemy import delete, select, update , create_engine
from bot.db.models import ViolationModel, FileModel, ViolationFile
from PIL import Image
import hashlib
import os
import shutil
from pathlib import Path

from bot.handlers.detection_handlers.detection_utils import get_image_orientation

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
    with Image.open(i) as img:
        orientation = get_image_orientation(img)
    session.add(FileModel(hash=i.stem, path=str(i), orientation=orientation ))
session.commit()

viols = session.execute(select(ViolationModel)).scalars().all()

for i in viols:
    session.add(ViolationFile(violation_id=i.id, file_hash=i.picture_hash))
session.commit()

