"""

Supabase database client and helper functions.

Falls back to local SQLite when Supabase is unreachable.

"""



import logging

import os

from functools import lru_cache

from typing import Any, Optional



from supabase import Client, create_client



from config import settings



logger = logging.getLogger(__name__)



_use_local: Optional[bool] = None





def _should_use_local_db() -> bool:

    """Determine whether to use local SQLite instead of Supabase."""

    global _use_local

    if _use_local is not None:

        return _use_local



    override = os.getenv("USE_LOCAL_DB", "").lower()

    if override in ("1", "true", "yes"):

        _use_local = True

        logger.warning("Using local SQLite database (USE_LOCAL_DB=true)")

        return True



    if not settings.supabase_url:

        _use_local = True

        logger.warning("SUPABASE_URL not set — using local SQLite database")

        return True



    key = settings.supabase_service_key or settings.supabase_key

    if not key:

        _use_local = True

        logger.warning("Supabase keys not set — using local SQLite database")

        return True



    try:

        client = create_client(settings.supabase_url, key)

        client.table("users").select("id").limit(1).execute()

        _use_local = False

        logger.info("Connected to Supabase")

    except Exception as exc:

        _use_local = True

        logger.warning("Supabase unavailable (%s) — using local SQLite database", exc)



    return _use_local





def init_database() -> None:

    """Initialize the active database backend."""

    if _should_use_local_db():

        from local_database import init_local_db



        init_local_db()





@lru_cache

def get_supabase_client() -> Client:

    """Create and cache the Supabase client (service role — bypasses RLS)."""

    if not settings.supabase_url:

        raise ValueError("SUPABASE_URL must be set in environment variables.")

    key = settings.supabase_service_key or settings.supabase_key

    if not key:

        raise ValueError("SUPABASE_SERVICE_KEY or SUPABASE_KEY must be set.")

    return create_client(settings.supabase_url, key)





@lru_cache

def get_supabase_admin() -> Client:

    """Admin client with service role key for privileged operations."""

    key = settings.supabase_service_key or settings.supabase_key

    return create_client(settings.supabase_url, key)





def fetch_one(table: str, filters: dict[str, Any]) -> Optional[dict]:

    """Fetch a single row matching filters."""

    if _should_use_local_db():

        from local_database import local_fetch_one



        return local_fetch_one(table, filters)



    client = get_supabase_client()

    query = client.table(table).select("*")

    for key, value in filters.items():

        query = query.eq(key, value)

    result = query.limit(1).execute()

    return result.data[0] if result.data else None





def fetch_all(

    table: str,

    filters: Optional[dict[str, Any]] = None,

    order_by: Optional[str] = None,

    ascending: bool = False,

) -> list[dict]:

    """Fetch all rows matching optional filters."""

    if _should_use_local_db():

        from local_database import local_fetch_all



        return local_fetch_all(table, filters, order_by, ascending)



    client = get_supabase_client()

    query = client.table(table).select("*")

    if filters:

        for key, value in filters.items():

            query = query.eq(key, value)

    if order_by:

        query = query.order(order_by, desc=not ascending)

    result = query.execute()

    return result.data or []





def insert_row(table: str, data: dict[str, Any]) -> dict:

    """Insert a row and return the created record."""

    if _should_use_local_db():

        from local_database import local_insert_row



        return local_insert_row(table, data)



    client = get_supabase_client()

    result = client.table(table).insert(data).execute()

    return result.data[0]





def update_row(table: str, row_id: str, data: dict[str, Any]) -> dict:

    """Update a row by id."""

    if _should_use_local_db():

        from local_database import local_update_row



        return local_update_row(table, row_id, data)



    client = get_supabase_client()

    result = client.table(table).update(data).eq("id", row_id).execute()

    return result.data[0] if result.data else {}





def delete_row(table: str, row_id: str) -> None:

    """Delete a row by id."""

    if _should_use_local_db():

        from local_database import local_delete_row



        local_delete_row(table, row_id)

        return



    client = get_supabase_client()

    client.table(table).delete().eq("id", row_id).execute()


