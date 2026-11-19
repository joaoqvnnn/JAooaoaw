import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Numeric, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DATABASE_URL, SUPER_ADMIN_ID


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), default="Membro")
    wallet_id: Mapped[str] = mapped_column(String(32), unique=True)
    balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UserState(Base):
    __tablename__ = "user_states"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # telegram_id
    screen: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deep_link_arg: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    pending_operation: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pending_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


engine = create_async_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = (
    async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    if engine
    else None
)


async def init_db() -> None:
    if not engine:
        raise RuntimeError("DATABASE_URL não configurado.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def gen_wallet_id() -> str:
    return "W" + secrets.token_hex(6).upper()


async def get_or_create_user(tg_user) -> User:
    async with SessionLocal() as session:
        row = (
            await session.execute(select(User).where(User.telegram_id == tg_user.id))
        ).scalar_one_or_none()

        is_root = tg_user.id == SUPER_ADMIN_ID

        if row is None:
            row = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name or "Membro",
                wallet_id=gen_wallet_id(),
                is_admin=is_root,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
        else:
            row.username = tg_user.username
            row.first_name = tg_user.first_name or row.first_name
            if is_root and not row.is_admin:
                row.is_admin = True
            row.last_activity = datetime.now(timezone.utc)
            await session.commit()
        return row


async def get_user_by_tg_id(telegram_id: int) -> Optional[User]:
    async with SessionLocal() as session:
        return (
            await session.execute(select(User).where(User.telegram_id == telegram_id))
        ).scalar_one_or_none()


async def get_state(user_id: int) -> Optional[UserState]:
    async with SessionLocal() as session:
        return await session.get(UserState, user_id)


async def upsert_state(user_id: int, **fields) -> UserState:
    async with SessionLocal() as session:
        state = await session.get(UserState, user_id)
        if state is None:
            state = UserState(user_id=user_id)
            session.add(state)
        for k, v in fields.items():
            setattr(state, k, v)
        state.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(state)
        return state


async def get_setting(key: str) -> Optional[str]:
    async with SessionLocal() as session:
        row = await session.get(Setting, key)
        return row.value if row else None


async def set_setting(key: str, value: str) -> None:
    async with SessionLocal() as session:
        row = await session.get(Setting, key)
        if row is None:
            row = Setting(key=key, value=value)
            session.add(row)
        else:
            row.value = value
        await session.commit()
