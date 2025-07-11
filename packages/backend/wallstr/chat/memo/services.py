from uuid import UUID

from sqlalchemy import sql

from wallstr.chat.memo.models import MemoModel, MemoSectionModel, MemoType
from wallstr.chat.models import ChatMessageModel, ChatMessageType
from wallstr.services import BaseService


class MemoService(BaseService):
    async def get_memo_by_message_id(self, message_id: UUID) -> MemoModel | None:
        async with self.tx():
            result = await self.db.execute(
                sql.select(MemoModel).filter_by(chat_message_id=message_id)
            )
        return result.scalar_one_or_none()

    async def create_memo(
        self,
        message: ChatMessageModel,
        user_prompt: str,
        memo_type: MemoType = MemoType.SHORT,
    ) -> MemoModel:
        if message.message_type != ChatMessageType.MEMO:
            raise ValueError("Message is not a memo")

        async with self.tx():
            result = await self.db.execute(
                sql.insert(MemoModel)
                .values(
                    user_id=message.user_id,
                    chat_id=message.chat_id,
                    chat_message_id=message.id,
                    user_prompt=user_prompt,
                    memo_type=memo_type,
                )
                .returning(MemoModel)
            )
        return result.scalar_one()

    async def create_memo_section(
        self,
        memo: MemoModel,
        group: str,
        aspect: str,
        prompt: str,
        content: str,
        index: int,
    ) -> MemoSectionModel:
        async with self.tx():
            result = await self.db.execute(
                sql.insert(MemoSectionModel)
                .values(
                    user_id=memo.user_id,
                    memo_id=memo.id,
                    chat_id=memo.chat_id,
                    group=group,
                    aspect=aspect,
                    prompt=prompt,
                    content=content,
                    index=index,
                )
                .returning(MemoSectionModel)
            )
        return result.scalar_one()
