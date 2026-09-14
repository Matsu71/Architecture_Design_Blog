/** Keep source coordinates unchanged; distinguish a building pin from an entrance. */
export function isJapanCoordinate(lat, lng) {
  return typeof lat === 'number' && typeof lng === 'number'
    && Number.isFinite(lat) && Number.isFinite(lng)
    && lat >= 20 && lat <= 46 && lng >= 122 && lng <= 154;
}

export function locationLabel(location = {}) {
  if (location.status === 'withheld') return '位置を確認中';
  if (location.status === 'cross-checked' && location.precision === 'building') return '建物位置を照合（入口未照合）';
  if (location.status === 'cross-checked' && location.precision === 'entrance') return '公開入口の位置を照合';
  if (location.status === 'cross-checked') return '施設位置を照合（入口未照合）';
  if (location.status === 'address-matched') return '施設座標（入口未照合）';
  return '位置を確認中';
}

/** Return all selectable records, never a cluster centroid or jittered coordinate. */
export function nearbyScreenPoints(records, anchor, project, radius = 24) {
  if (!anchor || !isJapanCoordinate(anchor.lat, anchor.lng) || typeof project !== 'function') return [];
  if (!Number.isFinite(radius) || radius < 0) return [];
  const origin = project(anchor);
  return records.filter(record => {
    if (!isJapanCoordinate(record?.lat, record?.lng) || record.location?.status === 'withheld') return false;
    const point = project(record);
    return Math.hypot(point.x - origin.x, point.y - origin.y) <= radius;
  });
}

/** Inclusive point-in-ring test. Ring positions use GeoJSON [longitude, latitude]. */
export function pointInRing(lat, lng, ring) {
  if (!isJapanCoordinate(lat, lng) || !Array.isArray(ring) || ring.length < 4) return false;
  if (!ring.every(p => Array.isArray(p) && p.length >= 2 && isJapanCoordinate(p[1], p[0]))) return false;
  if (ring[0][0] !== ring.at(-1)[0] || ring[0][1] !== ring.at(-1)[1]) return false;
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    const dx = xj - xi, dy = yj - yi;
    const cross = (lng - xi) * dy - (lat - yi) * dx;
    const length = Math.hypot(dx, dy);
    if (length > 0 && Math.abs(cross) <= 1e-10 * length
      && lng >= Math.min(xi, xj) - 1e-10 && lng <= Math.max(xi, xj) + 1e-10
      && lat >= Math.min(yi, yj) - 1e-10 && lat <= Math.max(yi, yj) + 1e-10) return true;
    if ((yi > lat) !== (yj > lat) && lng < (xj - xi) * (lat - yi) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
