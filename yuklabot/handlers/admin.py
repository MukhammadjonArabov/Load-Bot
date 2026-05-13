from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from config import config
from database.db import ban_user, get_all_users, get_stats, unban_user


router = Router()


def is_admin(user_id: int | None) -> bool:
    return bool(user_id and user_id in config.ADMIN_IDS)


@router.message(Command("admin"), F.from_user.id.in_(config.ADMIN_IDS))
async def admin_panel(message: Message) -> None:
    stats = await get_stats()
    await message.answer(
        "🛠 <b>Admin panel</b>\n\n"
        f"👥 Users: {stats['total_users']}\n"
        f"📥 Downloads: {stats['total_downloads']}\n"
        f"📆 Today: {stats['today_downloads']}\n\n"
        "Commands:\n"
        "/stats\n"
        "/users\n"
        "/broadcast message\n"
        "/ban user_id\n"
        "/unban user_id"
    )


@router.message(Command("stats"), F.from_user.id.in_(config.ADMIN_IDS))
async def stats_command(message: Message) -> None:
    stats = await get_stats()
    await message.answer(
        "📊 <b>Statistics</b>\n\n"
        f"👥 Total users: {stats['total_users']}\n"
        f"📥 Total downloads: {stats['total_downloads']}\n"
        f"📆 Today's downloads: {stats['today_downloads']}"
    )


@router.message(Command("users"), F.from_user.id.in_(config.ADMIN_IDS))
async def users_command(message: Message) -> None:
    users = await get_all_users()
    await message.answer(f"👥 Total active users: {len(users)}")


@router.message(Command("broadcast"), F.from_user.id.in_(config.ADMIN_IDS))
async def broadcast_command(message: Message, command: CommandObject) -> None:
    text = command.args
    if not text:
        await message.answer("Usage: /broadcast message")
        return

    users = await get_all_users()
    sent = 0
    failed = 0
    for user in users:
        try:
            await message.bot.send_message(user.id, text)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"✅ Broadcast sent: {sent}\n❌ Failed: {failed}")


@router.message(Command("ban"), F.from_user.id.in_(config.ADMIN_IDS))
async def ban_command(message: Message, command: CommandObject) -> None:
    user_id = _parse_user_id(command.args)
    if not user_id:
        await message.answer("Usage: /ban user_id")
        return
    updated = await ban_user(user_id)
    await message.answer("✅ User banned" if updated else "❌ User not found")


@router.message(Command("unban"), F.from_user.id.in_(config.ADMIN_IDS))
async def unban_command(message: Message, command: CommandObject) -> None:
    user_id = _parse_user_id(command.args)
    if not user_id:
        await message.answer("Usage: /unban user_id")
        return
    updated = await unban_user(user_id)
    await message.answer("✅ User unbanned" if updated else "❌ User not found")


def _parse_user_id(raw: str | None) -> int | None:
    if not raw:
        return None
    value = raw.strip().split()[0]
    if not value.isdigit():
        return None
    return int(value)
