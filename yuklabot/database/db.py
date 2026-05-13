from datetime import datetime, timezone

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from yuklabot.config import config
from yuklabot.database.models import Base, Download, User


engine = create_async_engine(config.database_url, echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await _archive_incompatible_schema(conn)
        await conn.run_sync(Base.metadata.create_all)


async def _archive_incompatible_schema(conn) -> None:
    users_columns = await conn.execute(
        text(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
            """
        )
    )
    columns = {row.column_name: row.data_type for row in users_columns}
    if not columns:
        return

    incompatible = "telegram_id" in columns or columns.get("id") not in {"bigint"}
    if not incompatible:
        return

    suffix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    await conn.execute(text("DROP TABLE IF EXISTS downloads CASCADE"))
    await conn.execute(text(f'ALTER TABLE users RENAME TO users_legacy_{suffix}'))


async def get_or_create_user(user_id: int, username: str | None, full_name: str, language: str = "uz") -> User:
    async with async_session() as session:
        user = await session.get(User, user_id)
        now = datetime.now(timezone.utc)
        if user:
            user.username = username
            user.full_name = full_name
            user.last_active = now
        else:
            user = User(
                id=user_id,
                username=username,
                full_name=full_name,
                language=language,
                last_active=now,
            )
            session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def add_download(
    user_id: int,
    platform: str,
    url: str,
    title: str,
    file_type: str,
    quality: str,
    file_size: float,
) -> Download:
    async with async_session() as session:
        download = Download(
            user_id=user_id,
            platform=platform,
            url=url,
            title=title[:512],
            file_type=file_type,
            quality=quality,
            file_size=file_size,
        )
        session.add(download)
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(downloads_count=User.downloads_count + 1, last_active=datetime.now(timezone.utc))
        )
        await session.commit()
        await session.refresh(download)
        return download


async def get_user_downloads(user_id: int, limit: int = 20) -> list[Download]:
    async with async_session() as session:
        result = await session.execute(
            select(Download)
            .where(Download.user_id == user_id)
            .order_by(Download.downloaded_at.desc(), Download.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_download_by_id(download_id: int, user_id: int) -> Download | None:
    async with async_session() as session:
        result = await session.execute(
            select(Download).where(Download.id == download_id, Download.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def get_stats() -> dict[str, int]:
    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        total_downloads = await session.scalar(select(func.count(Download.id)))
        today = datetime.now(timezone.utc).date()
        today_downloads = await session.scalar(
            select(func.count(Download.id)).where(func.date(Download.downloaded_at) == today)
        )
        return {
            "total_users": int(total_users or 0),
            "total_downloads": int(total_downloads or 0),
            "today_downloads": int(today_downloads or 0),
        }


async def get_all_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.is_banned.is_(False)).order_by(User.joined_at.asc()))
        return list(result.scalars().all())


async def ban_user(user_id: int) -> bool:
    return await _set_ban(user_id, True)


async def unban_user(user_id: int) -> bool:
    return await _set_ban(user_id, False)


async def _set_ban(user_id: int, is_banned: bool) -> bool:
    async with async_session() as session:
        result = await session.execute(update(User).where(User.id == user_id).values(is_banned=is_banned))
        await session.commit()
        return bool(result.rowcount)


async def update_last_active(user_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(last_active=datetime.now(timezone.utc))
        )
        await session.commit()


async def update_user_language(user_id: int, language: str) -> None:
    async with async_session() as session:
        await session.execute(update(User).where(User.id == user_id).values(language=language))
        await session.commit()
