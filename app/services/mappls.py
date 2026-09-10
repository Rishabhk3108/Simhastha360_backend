import httpx

from app.core.config import settings

ROUTE_API_BASE = "https://route.mappls.com/route/direction/route_adv/driving"


class RouteUnavailable(Exception):
    pass


# Standard Google/Mapbox-style encoded polyline decoder (precision 5) - Mappls'
# route geometry uses the same encoding. Mirrors the decoder in the mobile
# app's api/mappls.ts so both clients interpret routes identically.
def _decode_polyline(encoded: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    index = 0
    lat = 0
    lng = 0

    while index < len(encoded):
        result = 1
        shift = 0
        while True:
            b = ord(encoded[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1F:
                break
        lat += (~(result >> 1)) if (result & 1) else (result >> 1)

        result = 1
        shift = 0
        while True:
            b = ord(encoded[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1F:
                break
        lng += (~(result >> 1)) if (result & 1) else (result >> 1)

        points.append((lat * 1e-5, lng * 1e-5))
    return points


async def get_driving_route(
    from_lat: float, from_lng: float, to_lat: float, to_lng: float
) -> dict:
    """A plain point-to-point driving route (no zone-avoidance) - used to draw
    the manager-facing "volunteer is here, task is there" line, not to guide
    live navigation."""
    if not settings.mappls_key:
        raise RouteUnavailable("Mappls key is not configured on the backend")

    url = f"{ROUTE_API_BASE}/{from_lng},{from_lat};{to_lng},{to_lat}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            url,
            params={"geometries": "polyline", "overview": "full", "access_token": settings.mappls_key},
        )
    resp.raise_for_status()
    data = resp.json()
    routes = data.get("routes") or []
    if not routes:
        raise RouteUnavailable("No route found")

    route = routes[0]
    coordinates = [{"lat": lat, "lng": lng} for lat, lng in _decode_polyline(route["geometry"])]
    return {
        "coordinates": coordinates,
        "distance_km": route["distance"] / 1000,
        "duration_min": route["duration"] / 60,
    }
