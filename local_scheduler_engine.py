import os
import sys
import time
import json
import uuid
import sqlite3
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "bff.sqlite3"
MARKETING_OUTPUT_DIR = ROOT_DIR / "colorbox" / "marketing" / "output"
IMAGES_DIR = ROOT_DIR / "colorbox" / "colorbox-knowledge" / "images"

sys.path.append(str(ROOT_DIR / "colorbox" / "marketing"))
try:
    from gemini_visual_engine import render_final_carousel_package
except Exception:
    render_final_carousel_package = None

# No hardcoded fallback plans; all plans must come from real user/agent briefs.
DEFAULT_DAYS_PLAN = []

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn

def init_scheduler_db():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS local_schedules (
                id TEXT PRIMARY KEY,
                group_id TEXT DEFAULT 'marketing',
                campaign_title TEXT,
                total_days INTEGER DEFAULT 3,
                current_day INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active', -- active, paused, completed, cancelled
                trigger_mode TEXT DEFAULT 'daily', -- daily, interval
                interval_seconds INTEGER DEFAULT 86400,
                next_run_at REAL,
                last_run_at REAL DEFAULT 0,
                config_json TEXT DEFAULT '{}',
                created_at REAL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schedule_runs (
                id TEXT PRIMARY KEY,
                schedule_id TEXT,
                day_number INTEGER,
                run_at REAL,
                status TEXT,
                output_dir TEXT,
                summary TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()

def create_schedule(
    campaign_title: str = "Colorbox 3-Day Content Sprint",
    total_days: int = 3,
    interval_seconds: int = 86400,
    start_day1_now: bool = True,
    days_config: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    init_scheduler_db()
    conn = _connect()
    try:
        now = time.time()
        sched_id = f"sched-{uuid.uuid4().hex[:8]}"
        plan = days_config or []
        if not plan:
            raise ValueError("days_config wajib diisi dengan rencana produk dan tema nyata dari diskusi tim marketing.")
        cfg = json.dumps({"days": plan})

        if start_day1_now:
            # Day 1 is triggered immediately; Day 2 is scheduled for next interval
            next_run = now + interval_seconds
            current_day = 2 if total_days > 1 else 1
            status = "active" if total_days > 1 else "completed"
        else:
            # Day 1 is scheduled for future
            next_run = now + interval_seconds
            current_day = 1
            status = "active"

        conn.execute("""
            INSERT INTO local_schedules (
                id, group_id, campaign_title, total_days, current_day, status, 
                trigger_mode, interval_seconds, next_run_at, last_run_at, config_json, created_at
            ) VALUES (?, 'marketing', ?, ?, ?, ?, 'daily', ?, ?, ?, ?, ?)
        """, (sched_id, campaign_title, total_days, current_day, status, interval_seconds, next_run, now if start_day1_now else 0, cfg, now))
        conn.commit()

        # If day 1 starts now, render Day 1 assets immediately!
        if start_day1_now:
            _execute_day_render(sched_id, 1, plan[0])

        return get_schedule_by_id(sched_id)
    finally:
        conn.close()

def get_schedule_by_id(sched_id: str) -> Dict[str, Any]:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM local_schedules WHERE id = ?", (sched_id,)).fetchone()
        if not row:
            return {}
        return _format_schedule_dict(row, conn)
    finally:
        conn.close()

def get_all_schedules() -> List[Dict[str, Any]]:
    init_scheduler_db()
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM local_schedules ORDER BY created_at DESC").fetchall()
        return [_format_schedule_dict(r, conn) for r in rows]
    finally:
        conn.close()

def _format_schedule_dict(row: sqlite3.Row, conn: sqlite3.Connection) -> Dict[str, Any]:
    now = time.time()
    cfg = json.loads(row["config_json"] or "{}")
    days_plan = cfg.get("days", [])
    
    # Fetch runs
    runs = conn.execute(
        "SELECT * FROM schedule_runs WHERE schedule_id = ? ORDER BY day_number ASC",
        (row["id"],)
    ).fetchall()
    completed_days = {r["day_number"]: r for r in runs}

    days_status = []
    for d in days_plan:
        d_num = d["day"]
        if d_num in completed_days:
            st = "completed"
            run_time = completed_days[d_num]["run_at"]
        elif d_num == row["current_day"] and row["status"] == "active":
            st = "scheduled_next"
            run_time = row["next_run_at"]
        elif d_num > row["current_day"] and row["status"] == "active":
            st = "queued"
            run_time = row["next_run_at"] + ((d_num - row["current_day"]) * row["interval_seconds"])
        else:
            st = "pending"
            run_time = 0

        days_status.append({
            "day": d_num,
            "title": d.get("title", f"Day {d_num}"),
            "topic": d.get("topic", ""),
            "palette": d.get("palette", ""),
            "status": st,
            "target_time": time.strftime("%Y-%m-%d %H:%M WIB", time.localtime(run_time)) if run_time else "Menunggu",
            "preview_url": f"/output/carousel_day_{d_num}/carousel_preview.html" if st == "completed" else None
        })

    next_run = row["next_run_at"]
    countdown = max(0, int(next_run - now)) if (row["status"] == "active" and next_run > now) else 0

    return {
        "id": row["id"],
        "campaign_title": row["campaign_title"],
        "total_days": row["total_days"],
        "current_day": row["current_day"],
        "status": row["status"],
        "interval_seconds": row["interval_seconds"],
        "next_run_at": next_run,
        "next_run_formatted": time.strftime("%A, %d %B %Y - %H:%M WIB", time.localtime(next_run)) if next_run else "-",
        "countdown_seconds": countdown,
        "countdown_human": f"{countdown // 3600} jam {(countdown % 3600) // 60} menit" if countdown > 3600 else f"{countdown // 60} menit {countdown % 60} detik",
        "created_at_formatted": time.strftime("%Y-%m-%d %H:%M WIB", time.localtime(row["created_at"])),
        "days": days_status
    }

def _execute_day_render(schedule_id: str, day_num: int, day_info: dict) -> None:
    """Renders Day X assets to disk and records execution in database."""
    day_dir = MARKETING_OUTPUT_DIR / f"carousel_day_{day_num}"
    os.makedirs(day_dir, exist_ok=True)
    
    # Products for this day
    prods = day_info.get("products")

    if render_final_carousel_package:
        try:
            render_final_carousel_package(
                theme_title=day_info.get("title", f"DAY {day_num}"),
                headline=f"Spotlight Day {day_num}",
                subtitle=day_info.get("topic", "Lookbook"),
                products_info=prods or [],
                output_dir=str(day_dir),
                images_dir=str(IMAGES_DIR),
                day_num=day_num
            )
            # Also update carousel_latest
            render_final_carousel_package(
                theme_title=day_info.get("title", f"DAY {day_num}"),
                headline=f"Spotlight Day {day_num}",
                subtitle=day_info.get("topic", "Lookbook"),
                products_info=prods or [],
                output_dir=str(MARKETING_OUTPUT_DIR / "carousel_latest"),
                images_dir=str(IMAGES_DIR),
                day_num=day_num
            )
        except Exception as e:
            print(f"[Local Scheduler Render Error Day {day_num}]: {e}")

    # Record run in schedule_runs
    conn = _connect()
    try:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        now = time.time()
        conn.execute("""
            INSERT OR REPLACE INTO schedule_runs (id, schedule_id, day_number, run_at, status, output_dir, summary)
            VALUES (?, ?, ?, ?, 'completed', ?, ?)
        """, (run_id, schedule_id, day_num, now, str(day_dir), f"Day {day_num}: {day_info.get('title')}"))
        
        # Inject notification into marketing group chat
        msg_id = f"sch-msg-{uuid.uuid4().hex[:8]}"
        post_text = (
            f"⏰ **[LOCAL SCHEDULER — DAY {day_num} SELESAI DIRENDER!]**\n\n"
            f"Pipeline otomatis lokal berhasil memproduksi aset konten **Hari ke-{day_num}**:\n"
            f"- **Tema:** {day_info.get('title')}\n"
            f"- **Topik:** {day_info.get('topic')}\n"
            f"- **Palet Warna:** {day_info.get('palette')}\n\n"
            f"![Cover Day {day_num}](/output/carousel_day_{day_num}/slide_1_cover_hero.png)\n\n"
            f"👉 **[Buka Live Interactive Preview Day {day_num}](/output/carousel_day_{day_num}/carousel_preview.html)**"
        )
        conn.execute("""
            INSERT INTO group_messages (id, group_id, sender, sender_type, content, created_at, author, bot_id, text)
            VALUES (?, 'marketing', 'vina', 'bot', ?, ?, 'Vina', 'vina', ?)
        """, (msg_id, post_text, now, post_text))
        conn.commit()
    finally:
        conn.close()

def trigger_next_day(schedule_id: str) -> Dict[str, Any]:
    """Manually forces immediate trigger of the next scheduled day without waiting."""
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM local_schedules WHERE id = ?", (schedule_id,)).fetchone()
        if not row:
            return {"error": "Schedule not found"}

        current_day = row["current_day"]
        total_days = row["total_days"]
        if current_day > total_days:
            conn.execute("UPDATE local_schedules SET status = 'completed' WHERE id = ?", (schedule_id,))
            conn.commit()
            return {"status": "completed", "message": "Semua hari sudah selesai"}

        cfg = json.loads(row["config_json"] or "{}")
        plan = cfg.get("days", [])
        if not plan or current_day > len(plan):
            return {"error": f"Tidak ada rencana untuk hari ke-{current_day}"}
        day_info = plan[current_day - 1]

        now = time.time()
        _execute_day_render(schedule_id, current_day, day_info)

        if current_day < total_days:
            next_day = current_day + 1
            next_run = now + row["interval_seconds"]
            conn.execute("""
                UPDATE local_schedules 
                SET current_day = ?, next_run_at = ?, last_run_at = ?, status = 'active'
                WHERE id = ?
            """, (next_day, next_run, now, schedule_id))
        else:
            conn.execute("""
                UPDATE local_schedules 
                SET last_run_at = ?, status = 'completed', current_day = ?
                WHERE id = ?
            """, (now, total_days + 1, schedule_id))
        conn.commit()

        return get_schedule_by_id(schedule_id)
    finally:
        conn.close()

def pause_schedule(schedule_id: str) -> Dict[str, Any]:
    conn = _connect()
    try:
        conn.execute("UPDATE local_schedules SET status = 'paused' WHERE id = ?", (schedule_id,))
        conn.commit()
        return get_schedule_by_id(schedule_id)
    finally:
        conn.close()

def resume_schedule(schedule_id: str) -> Dict[str, Any]:
    conn = _connect()
    try:
        conn.execute("UPDATE local_schedules SET status = 'active' WHERE id = ?", (schedule_id,))
        conn.commit()
        return get_schedule_by_id(schedule_id)
    finally:
        conn.close()

def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    conn = _connect()
    try:
        conn.execute("UPDATE local_schedules SET status = 'cancelled' WHERE id = ?", (schedule_id,))
        conn.commit()
        return {"status": "cancelled", "id": schedule_id}
    finally:
        conn.close()

_DAEMON_STARTED = False

def start_scheduler_daemon() -> None:
    global _DAEMON_STARTED
    if _DAEMON_STARTED:
        return
    _DAEMON_STARTED = True

    def daemon_worker():
        while True:
            time.sleep(5)
            try:
                now = time.time()
                conn = _connect()
                try:
                    due_rows = conn.execute("""
                        SELECT id, current_day, total_days FROM local_schedules 
                        WHERE status = 'active' AND next_run_at > 0 AND next_run_at <= ?
                    """, (now,)).fetchall()
                finally:
                    conn.close()

                for r in due_rows:
                    if r["current_day"] <= r["total_days"]:
                        print(f"[Local Scheduler Daemon] Auto-triggering schedule {r['id']} Day {r['current_day']}")
                        trigger_next_day(r["id"])
            except Exception as e:
                print(f"[Local Scheduler Daemon Exception]: {e}")

    t = threading.Thread(target=daemon_worker, daemon=True, name="LocalSchedulerDaemon")
    t.start()
    print("[Local Scheduler Engine] Background daemon thread successfully started.")
