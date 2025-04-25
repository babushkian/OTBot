"""Модели OTBot."""


from sqlalchemy import TEXT, BIGINT, String, ForeignKey, LargeBinary, true, false
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy.dialects.sqlite import JSON

from bot.enums import UserRole, ViolationStatus, ViolationCategory
from bot.db.database import Base


class UserModel(Base):
    """Модель пользователя."""

    telegram_id: Mapped[int] = mapped_column(BIGINT, unique=True)
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]
    phone_number: Mapped[str | None]

    user_role: Mapped[UserRole] = mapped_column(default=UserRole.USER)
    is_approved: Mapped[bool] = mapped_column(default=False, server_default=false())  # одобрен
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())  # активен
    telegram_data: Mapped[dict | None] = mapped_column(JSON)  # данные из telegram
    user_description: Mapped[str | None]

    responsible_area: Mapped[list["AreaModel"]] = relationship("AreaModel", back_populates="responsible_user")
    violations: Mapped[list["ViolationModel"]] = relationship("ViolationModel", back_populates="detector")

    def __str__(self) -> str:
        """Строковое представление."""
        return self.__class__.__name__ + f"({self.first_name} {self.last_name})"


class ViolationModel(Base):
    """Модель обнаруженных нарушений."""

    detector_id: Mapped[int] = mapped_column(ForeignKey("usermodel.id", name="fk_detector_user_id"))
    detector: Mapped["UserModel"] = relationship("UserModel", back_populates="violations")

    area_id: Mapped[int] = mapped_column(ForeignKey("areamodel.id", name="fk_violation_area_id"))
    area: Mapped["AreaModel"] = relationship("AreaModel", back_populates="violations")

    picture: Mapped[bytes] = mapped_column(LargeBinary)
    description: Mapped[str] = mapped_column(String(200))
    status: Mapped[ViolationStatus] = mapped_column(default=ViolationStatus.ACTIVE)
    category: Mapped[ViolationCategory]
    actions_needed: Mapped[str] = mapped_column(TEXT)

    def __str__(self) -> str:
        """Строковое представление."""
        return self.__class__.__name__ + f"({self.description})"


class AreaModel(Base):
    """Модель места нарушения."""

    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str]
    violations: Mapped[list["ViolationModel"]] = relationship("ViolationModel", back_populates="area")

    responsible_user_id: Mapped[int] = mapped_column(ForeignKey("usermodel.id",
                                                                name="fk_area_responsible_user_id"))
    responsible_user: Mapped["UserModel"] = relationship("UserModel", back_populates="responsible_area")

    def __str__(self) -> str:
        """Строковое представление."""
        return self.__class__.__name__ + f"({self.name})"

# print(AreaModel.__tablename__)


# class ActionModel(Base):
#     """Модель мероприятий по устранению нарушений."""
#     name: Mapped[str] = mapped_column(String(100), unique=True)
#     description: Mapped[str]

# image: Mapped[list["Image"]] = relationship("Image", back_populates="user")


# class Image(Base):
#     """Модель изображения."""
#
#     user_id: Mapped[int] = mapped_column(ForeignKey("user.id", name="fk_image_user_id"))
#     user: Mapped["UserModel"] = relationship("UserModel", back_populates="image")
#
#     name: Mapped[str] = mapped_column(String(100))
#     data: Mapped[bytes] = mapped_column(LargeBinary)
#
#     def __str__(self) -> str:
#         """Строковое представление."""
#         return self.__class__.__name__ + f"({self.name}"
