import asyncio
from datetime import UTC, datetime, timedelta
from pymongo.errors import PyMongoError
from app.tools.mongo_tool import _collection, MongoStoreError

FUNNEL_STATUSES = ["new", "contacted", "interested", "follow_up", "not_interested", "converted"]

async def get_lead_funnel_by_status(days: int) -> dict:
    now = datetime.now(UTC)
    from_date = now - timedelta(days=days)

    def run_aggregation():
        pipeline = [
            {"$match": {"createdAt": {"$gte": from_date, "$lte": now}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        return list(_collection("leads").aggregate(pipeline))

    try:
        results = await asyncio.to_thread(run_aggregation)
    except PyMongoError as exc:
        raise MongoStoreError("failed to fetch lead funnel") from exc

    status_map = {r["_id"]: r["count"] for r in results}
    return {
        "data": [{"status": s, "count": status_map.get(s, 0)} for s in FUNNEL_STATUSES],
        "date_range": {
            "from": from_date.strftime("%Y-%m-%d"),
            "to": now.strftime("%Y-%m-%d"),
        }
    }