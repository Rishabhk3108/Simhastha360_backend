GRID_SIZE_DEGREES = 0.003  # roughly ~300m, coarse enough for a Ujjain-scale demo


def grid_cluster(points: list[tuple[float, float]], min_cluster_size: int = 3):
    """Bucket points into a lat/lng grid as a lightweight stand-in for k-means -
    good enough to surface "reports piling up here" without pulling in numpy/sklearn.
    """
    buckets: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for lat, lng in points:
        key = (round(lat / GRID_SIZE_DEGREES), round(lng / GRID_SIZE_DEGREES))
        buckets.setdefault(key, []).append((lat, lng))

    clusters = []
    for pts in buckets.values():
        if len(pts) < min_cluster_size:
            continue
        avg_lat = sum(p[0] for p in pts) / len(pts)
        avg_lng = sum(p[1] for p in pts) / len(pts)
        clusters.append({"lat": avg_lat, "lng": avg_lng, "count": len(pts)})

    return sorted(clusters, key=lambda c: c["count"], reverse=True)
