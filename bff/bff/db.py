import asyncio
from pathlib import Path

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from . import config

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"
pool: AsyncConnectionPool | None = None


async def open_pool() -> None:
    global pool
    pool = AsyncConnectionPool(config.DATABASE_URL, min_size=1, max_size=10, open=False,
                               check=AsyncConnectionPool.check_connection, max_idle=300,
                               kwargs={"row_factory": dict_row, "autocommit": True})
    await pool.open(wait=True, timeout=10)
    await migrate()


async def close_pool() -> None:
    if pool:
        await pool.close()


async def migrate() -> None:
    await ex("create table if not exists schema_migrations (name text primary key, applied_at timestamptz default now())")
    done = {r["name"] for r in await q("select name from schema_migrations")}
    for f in sorted(MIGRATIONS.glob("*.sql")):
        if f.name in done:
            continue
        async with pool.connection() as c:
            async with c.transaction():
                await c.execute(f.read_text(encoding="utf-8"))
                await c.execute("insert into schema_migrations (name) values (%s)", (f.name,))


async def q(sql: str, *params) -> list[dict]:
    async with pool.connection() as c:
        cur = await c.execute(sql, params)
        return await cur.fetchall() if cur.description else []


async def q1(sql: str, *params) -> dict | None:
    rows = await q(sql, *params)
    return rows[0] if rows else None


async def ex(sql: str, *params) -> None:
    async with pool.connection() as c:
        await c.execute(sql, params)


async def ping() -> bool:
    try:
        await asyncio.wait_for(q("select 1"), 10)
        return True
    except Exception:
        return False


async def cleanup_loop() -> None:
    """Delete tool-event logs older than 90 days, now and then daily."""
    while True:
        try:
            await ex("delete from run_events where created_at < now() - interval '90 days'")
        except Exception:
            pass
        await asyncio.sleep(86400)
