import html
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from .config import config
from .db import SessionLocal, Draft
from .upwork_client import upwork
from .llm import generate_draft
from datetime import datetime

logging.basicConfig(level=logging.INFO)
# httpx logs every request URL, and Telegram URLs contain the bot token.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Upwork Agent is running. Drafts will appear here.\n\nSend /test to generate a sample draft.")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a sample draft and send it with Approve/Reject buttons."""
    fake_client_message = "Hi, I saw your profile and I'm interested in your services. Can you help me with a data analytics project?"
    fake_history = []
    draft_text = generate_draft(fake_client_message, fake_history)

    db = SessionLocal()
    try:
        draft = Draft(
            room_id="test_room",
            room_name="Test Room",
            client_message=fake_client_message,
            draft_text=draft_text,
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        # Send notification with buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve & Send", callback_data=f"approve_{draft.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{draft.id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            f"📩 <b>Test Draft</b>\n"
            f"Room: Test Room\n\n"
            f"<b>Client:</b>\n{html.escape(fake_client_message)}\n\n"
            f"<b>Draft reply:</b>\n{html.escape(draft_text)}"
        )
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
        print(f"[TELEGRAM] Test draft #{draft.id} sent")
    except Exception as e:
        await update.message.reply_text(f"Failed to generate test draft: {e}")
        print(f"[TELEGRAM] Test failed: {e}")
    finally:
        db.close()

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # format: approve_<id> or reject_<id>
    action, draft_id_str = data.split("_", 1)
    draft_id = int(draft_id_str)

    db = SessionLocal()
    try:
        draft = db.query(Draft).filter(Draft.id == draft_id).first()
        if not draft:
            await query.edit_message_text("Draft not found.")
            return

        if draft.status != "pending":
            # Guards against a double tap sending the same reply twice.
            await query.edit_message_text(f"This draft was already handled ({draft.status}).")
            return

        if action == "approve":
            if draft.room_id == "test_room":
                draft.status = "sent"
                draft.sent_at = datetime.utcnow()
                db.commit()
                await query.edit_message_text(f"✅ Test approved! (Not sent to Upwork)\n\n{draft.draft_text}")
            else:
                try:
                    result = upwork.send_message(draft.room_id, draft.draft_text)
                    draft.status = "sent"
                    draft.sent_at = datetime.utcnow()
                    draft.upwork_message_id = result.get("createRoomStoryV2", {}).get("id")
                    db.commit()
                    await query.edit_message_text(f"✅ Message sent successfully!\n\n{draft.draft_text}")
                except Exception as e:
                    draft.status = "failed"
                    db.commit()
                    await query.edit_message_text(f"❌ Failed to send: {str(e)}")
        elif action == "reject":
            draft.status = "rejected"
            db.commit()
            await query.edit_message_text("❌ Draft rejected.")
    finally:
        db.close()

def send_draft_notification(draft: Draft):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Token or Chat ID missing — skipping notification")
        return

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve & Send", callback_data=f"approve_{draft.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{draft.id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        f"📩 <b>New Upwork Draft</b>\n"
        f"Room: {html.escape(draft.room_name or draft.room_id or '')}\n\n"
        f"<b>Client:</b>\n{html.escape(draft.client_message[:400])}{'...' if len(draft.client_message) > 400 else ''}\n\n"
        f"<b>Draft reply:</b>\n{html.escape(draft.draft_text)}"
    )

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup.to_dict(),
    }
    try:
        resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        print(f"[TELEGRAM] Draft #{draft.id} notification sent")
    except Exception as e:
        print(f"[TELEGRAM] Failed to send notification: {e}")

def run_bot():
    if not config.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set — skipping Telegram bot")
        return

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CallbackQueryHandler(handle_approval))
    print("Starting Telegram bot...")
    application.run_polling()
