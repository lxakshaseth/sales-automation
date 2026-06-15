from app.core.rate_limiter import check_rate_limit
from app.exceptions.optimization_exceptions import OptimizationRateLimitError


class OptimizationRateLimiter:
    """Thin R10 facade over the existing distributed Redis rate limiter."""

    async def check(
        self,
        identifier: str,
        *,
        scope: str = "optimization",
        limit_type: str = "api",
        limit: int | None = None,
        window_seconds: int | None = None,
        increment: bool = True,
    ) -> dict:
        result = await check_rate_limit(
            identifier,
            scope=scope,
            limit_type=limit_type,
            limit=limit,
            window_seconds=window_seconds,
            increment=increment,
        )
        if not result["allowed"]:
            raise OptimizationRateLimitError("optimization rate limit exceeded")
        return result

