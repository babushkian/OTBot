from dataclasses import asdict
from sqlalchemy.ext.asyncio import AsyncSession

from bot.constants import action_needed_deadline
from bot.db.models import FileModel, ViolationModel
from bot.repositories.violation_repo import ViolationRepository
from bot.repositories.image_repo import ImageRepository
from bot.utils.image_utils import handle_image


class ViolationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.violations = ViolationRepository(session)
        self.images = ImageRepository(session)


    async def add(self, data):
        actions = [f"{line["action"]}. Срок устранения: {line["fix_time"]}" for line in action_needed_deadline()]
        violation = ViolationModel(area_id=data["area_id"],
                           description=data["description"],
                           detector_id=data["detector_id"],
                           category=data["category"],


                           picture=data["images"][0],


                           status=data["status"],
                           actions_needed=",\n".join(actions[index - 1] for index in data["actions_needed"]),
                        )

        self.session.add(violation)
        for image in data["images"]:
            image_info = handle_image(image)
            existing_file = await self.images.get(image_info.hash)
            # if existing_file:
            #     img_file = existing_file
            # else:
            #     img_file = FileModel(**asdict(image_info))
            #     await self.images.add(img_file)


            img_file = FileModel(**asdict(image_info))
            await self.images.add(img_file)


            with self.session.no_autoflush:
                violation.files.append(img_file)


        await self.session.commit()
        return violation

