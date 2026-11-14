import time
from datetime import datetime
from .upwork_client import upwork
from .llm import generate_draft
from .db import SessionLocal, Draft
from .telegram_bot import send_draft_notification
from .config import config

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

        print(f"Found room with unread: {room_name} ({room_id})")
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
        client_msg = latest.get("message", "")
        if not client_msg:
            continue

        # Build simple history
        history_lines = []
        for se in reversed(story_edges[1:6]):  # previous few
            n = se.get("node", {})
            history_lines.append(n.get("message", ""))
        history = "\n".join(history_lines)

        draft_text = generate_draft(client_msg, history)

        db = SessionLocal()
        try:
            draft = Draft(
                room_id=room_id,
                room_name=room_name,
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
    print("Starting Upwork poller...")
    while True:
        process_new_messages()
        time.sleep(config.POLL_INTERVAL_SECONDS)
