import time
import traceback
from datetime import datetime
from .upwork_client import upwork
from .llm import generate_draft
from .db import SessionLocal, Draft
from .telegram_bot import send_draft_notification
from .config import config

# Set after every completed poll cycle; the health endpoint reads it.
last_poll_at = 0.0


def _already_drafted(db, room_id, story_id, client_msg):
    """True if this exact client message already has a draft (any status)."""
    q = db.query(Draft).filter(Draft.room_id == room_id)
    if story_id:
        return q.filter(Draft.story_id == story_id).first() is not None
    return q.filter(Draft.client_message == client_msg).first() is not None


def process_new_messages():
    print(f"[{datetime.utcnow()}] Polling Upwork rooms...")
    try:
        rooms_data = upwork.list_rooms(limit=15)
        edges = rooms_data.get("roomList", {}).get("edges", [])
    except Exception as e:
        print(f"Failed to list rooms: {e}")
        return

    for edge in edges:
        node = edge.get("node", {})
        room_id = node.get("id")
        room_name = node.get("roomName") or node.get("topic")
        num_unread = node.get("numUnread", 0)

        if num_unread == 0:
            continue

        try:
            stories = upwork.get_room_stories(room_id, limit=10)
            story_edges = stories.get("roomStories", {}).get("edges", [])
        except Exception as e:
            print(f"Failed to get stories for {room_id}: {e}")
            continue

        if not story_edges:
            continue

        # Take the latest message as the one to reply to
        latest = story_edges[0].get("node", {})
        story_id = latest.get("id")
        client_msg = latest.get("message", "")
        if not client_msg:
            continue

        db = SessionLocal()
        try:
            # The room stays unread until someone opens it on Upwork, so
            # without this check every poll would draft the same message again.
            if _already_drafted(db, room_id, story_id, client_msg):
                continue

            print(f"Found new unread message in: {room_name} ({room_id})")

            # Build simple history
            history_lines = []
            for se in reversed(story_edges[1:6]):  # previous few
                n = se.get("node", {})
                history_lines.append(n.get("message", ""))
            history = "\n".join(history_lines)

            try:
                draft_text = generate_draft(client_msg, history)
            except Exception as e:
                # Not recorded as drafted, so the next poll retries it.
                print(f"Draft generation failed for room {room_id}: {e}")
                continue

            draft = Draft(
                room_id=room_id,
                room_name=room_name,
                story_id=story_id,
                client_message=client_msg,
                draft_text=draft_text,
                status="pending",
            )
            db.add(draft)
            db.commit()
            db.refresh(draft)
            print(f"Created draft #{draft.id} for room {room_id}")
            send_draft_notification(draft)
        finally:
            db.close()


def run_poller():
    global last_poll_at
    print("Starting Upwork poller...")
    while True:
        try:
            process_new_messages()
        except Exception:
            # Never let one bad cycle kill the polling thread.
            print("Poll cycle crashed:")
            traceback.print_exc()
        last_poll_at = time.time()
        time.sleep(config.POLL_INTERVAL_SECONDS)
