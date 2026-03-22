use pyo3::prelude::*;
use std::f64::consts::PI;

const EARTH_RADIUS_M: f64 = 6_371_000.0;

/// Haversine distance in meters between two points (decimal degrees).
#[inline]
fn haversine(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    let dlat = (lat2 - lat1) * PI / 180.0;
    let dlon = (lon2 - lon1) * PI / 180.0;
    let lat1_rad = lat1 * PI / 180.0;
    let lat2_rad = lat2 * PI / 180.0;

    let a = (dlat / 2.0).sin().powi(2)
        + lat1_rad.cos() * lat2_rad.cos() * (dlon / 2.0).sin().powi(2);
    EARTH_RADIUS_M * 2.0 * a.sqrt().atan2((1.0 - a).sqrt())
}

/// Compute discrete Frechet distance between two GPS tracks.
///
/// Takes two flat arrays [lat0, lon0, lat1, lon1, ...] and returns
/// the Frechet distance in meters.
#[pyfunction]
fn frechet_distance(track_a: Vec<f64>, track_b: Vec<f64>) -> PyResult<f64> {
    let n = track_a.len() / 2;
    let m = track_b.len() / 2;

    if n == 0 || m == 0 {
        return Ok(f64::INFINITY);
    }

    // Compute pairwise distance matrix
    let mut dist = vec![0.0f64; n * m];
    for i in 0..n {
        let la = track_a[i * 2];
        let lo = track_a[i * 2 + 1];
        for j in 0..m {
            let lb = track_b[j * 2];
            let lb_lon = track_b[j * 2 + 1];
            dist[i * m + j] = haversine(la, lo, lb, lb_lon);
        }
    }

    // Dynamic programming
    let mut dp = vec![f64::INFINITY; n * m];
    dp[0] = dist[0];

    for i in 1..n {
        dp[i * m] = dp[(i - 1) * m].max(dist[i * m]);
    }
    for j in 1..m {
        dp[j] = dp[j - 1].max(dist[j]);
    }
    for i in 1..n {
        for j in 1..m {
            let prev = dp[(i - 1) * m + j]
                .min(dp[i * m + (j - 1)])
                .min(dp[(i - 1) * m + (j - 1)]);
            dp[i * m + j] = prev.max(dist[i * m + j]);
        }
    }

    Ok(dp[n * m - 1])
}

/// Batch: compute Frechet distance between one reference track and multiple candidate tracks.
///
/// Returns a Vec of distances in meters, one per candidate.
/// Each track is a flat array [lat0, lon0, lat1, lon1, ...].
#[pyfunction]
fn frechet_distance_batch(
    reference: Vec<f64>,
    candidates: Vec<Vec<f64>>,
) -> PyResult<Vec<f64>> {
    let results: Vec<f64> = candidates
        .iter()
        .map(|c| {
            frechet_distance_inner(&reference, c)
        })
        .collect();
    Ok(results)
}

/// Inner Frechet computation (no PyResult wrapper).
fn frechet_distance_inner(track_a: &[f64], track_b: &[f64]) -> f64 {
    let n = track_a.len() / 2;
    let m = track_b.len() / 2;

    if n == 0 || m == 0 {
        return f64::INFINITY;
    }

    let mut dist = vec![0.0f64; n * m];
    for i in 0..n {
        let la = track_a[i * 2];
        let lo = track_a[i * 2 + 1];
        for j in 0..m {
            let lb = track_b[j * 2];
            let lb_lon = track_b[j * 2 + 1];
            dist[i * m + j] = haversine(la, lo, lb, lb_lon);
        }
    }

    let mut dp = vec![f64::INFINITY; n * m];
    dp[0] = dist[0];

    for i in 1..n {
        dp[i * m] = dp[(i - 1) * m].max(dist[i * m]);
    }
    for j in 1..m {
        dp[j] = dp[j - 1].max(dist[j]);
    }
    for i in 1..n {
        for j in 1..m {
            let prev = dp[(i - 1) * m + j]
                .min(dp[i * m + (j - 1)])
                .min(dp[(i - 1) * m + (j - 1)]);
            dp[i * m + j] = prev.max(dist[i * m + j]);
        }
    }

    dp[n * m - 1]
}

/// Convert Garmin semicircles to decimal degrees.
#[pyfunction]
fn semicircles_to_degrees(semicircles: f64) -> f64 {
    semicircles * (180.0 / 2_147_483_648.0)
}

/// Downsample a GPS track to approximately target_spacing_m between points.
///
/// Takes flat array [lat0, lon0, lat1, lon1, ...] and returns downsampled flat array.
#[pyfunction]
fn downsample_track(coords: Vec<f64>, target_spacing_m: f64) -> PyResult<Vec<f64>> {
    let n = coords.len() / 2;
    if n == 0 {
        return Ok(vec![]);
    }

    let mut result = vec![coords[0], coords[1]];
    let mut last_lat = coords[0];
    let mut last_lon = coords[1];
    let mut accum = 0.0;

    for i in 1..n {
        let lat = coords[i * 2];
        let lon = coords[i * 2 + 1];
        accum += haversine(last_lat, last_lon, lat, lon);
        last_lat = lat;
        last_lon = lon;

        if accum >= target_spacing_m {
            result.push(lat);
            result.push(lon);
            accum = 0.0;
        }
    }

    // Always include last point
    let last_idx = n - 1;
    if accum > target_spacing_m * 0.1 {
        result.push(coords[last_idx * 2]);
        result.push(coords[last_idx * 2 + 1]);
    }

    Ok(result)
}

/// Find all activities that match a reference track within a Frechet distance threshold.
///
/// Reads GPS data directly from the SQLite database, downsamples each activity track,
/// computes Frechet distance, and returns matches. Does everything in Rust — no Python overhead.
///
/// Args:
///     db_path: path to cycling_power.db
///     reference_track: flat array [lat0, lon0, lat1, lon1, ...] in decimal degrees (downsampled)
///     ref_bbox: (lat_min, lat_max, lon_min, lon_max) of reference track
///     threshold_m: maximum Frechet distance to consider a match (default 2000m)
///     spacing_m: target spacing for downsampling activity tracks (default 1000m)
///
/// Returns: Vec of (activity_id, frechet_distance_m)
#[pyfunction]
#[pyo3(signature = (db_path, reference_track, ref_bbox, threshold_m=2000.0, spacing_m=1000.0))]
fn find_matching_activities(
    db_path: &str,
    reference_track: Vec<f64>,
    ref_bbox: (f64, f64, f64, f64),
    threshold_m: f64,
    spacing_m: f64,
) -> PyResult<Vec<(i64, f64)>> {
    let conn = rusqlite::Connection::open(db_path)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("DB open failed: {}", e)))?;

    let semicircle_to_deg: f64 = 180.0 / 2_147_483_648.0;
    let bbox_margin = 0.05; // ~5km in degrees

    // Get all activity IDs that have GPS data
    let mut stmt = conn.prepare(
        "SELECT DISTINCT activity_id FROM records WHERE latitude IS NOT NULL AND latitude != 0"
    ).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{}", e)))?;

    let activity_ids: Vec<i64> = stmt.query_map([], |row| row.get(0))
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{}", e)))?
        .filter_map(|r| r.ok())
        .collect();

    let mut matches = Vec::new();
    let mut track_stmt = conn.prepare(
        "SELECT latitude, longitude FROM records \
         WHERE activity_id = ? AND latitude IS NOT NULL AND latitude != 0 \
         ORDER BY rowid"
    ).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{}", e)))?;

    for act_id in &activity_ids {
        // Load raw GPS points
        let rows: Vec<(f64, f64)> = track_stmt.query_map([act_id], |row| {
            Ok((row.get::<_, f64>(0)?, row.get::<_, f64>(1)?))
        })
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{}", e)))?
        .filter_map(|r| r.ok())
        .collect();

        if rows.len() < 10 {
            continue;
        }

        // Detect format: semicircles (abs > 1000) vs degrees (abs < 180)
        let is_semicircles = rows[0].0.abs() > 1000.0;
        let lats: Vec<f64> = if is_semicircles {
            rows.iter().map(|(lat, _)| lat * semicircle_to_deg).collect()
        } else {
            rows.iter().map(|(lat, _)| *lat).collect()
        };
        let lons: Vec<f64> = if is_semicircles {
            rows.iter().map(|(_, lon)| lon * semicircle_to_deg).collect()
        } else {
            rows.iter().map(|(_, lon)| *lon).collect()
        };

        // Quick bounding box check
        let lat_min = lats.iter().cloned().fold(f64::INFINITY, f64::min);
        let lat_max = lats.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let lon_min = lons.iter().cloned().fold(f64::INFINITY, f64::min);
        let lon_max = lons.iter().cloned().fold(f64::NEG_INFINITY, f64::max);

        if lat_max < ref_bbox.0 - bbox_margin || lat_min > ref_bbox.1 + bbox_margin
            || lon_max < ref_bbox.2 - bbox_margin || lon_min > ref_bbox.3 + bbox_margin
        {
            continue;
        }

        // Downsample
        let mut ds = vec![lats[0], lons[0]];
        let mut last_lat = lats[0];
        let mut last_lon = lons[0];
        let mut accum = 0.0;

        for i in 1..lats.len() {
            let d = haversine(last_lat, last_lon, lats[i], lons[i]);
            accum += d;
            last_lat = lats[i];
            last_lon = lons[i];

            if accum >= spacing_m {
                ds.push(lats[i]);
                ds.push(lons[i]);
                accum = 0.0;
            }
        }
        if accum > spacing_m * 0.1 {
            ds.push(*lats.last().unwrap());
            ds.push(*lons.last().unwrap());
        }

        if ds.len() < 10 {
            continue;
        }

        // Compute Frechet distance
        let fd = frechet_distance_inner(&reference_track, &ds);
        if fd <= threshold_m {
            matches.push((*act_id, fd));
        }
    }

    // Sort by distance
    matches.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
    Ok(matches)
}

#[pymodule]
fn frechet_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(frechet_distance, m)?)?;
    m.add_function(wrap_pyfunction!(frechet_distance_batch, m)?)?;
    m.add_function(wrap_pyfunction!(semicircles_to_degrees, m)?)?;
    m.add_function(wrap_pyfunction!(downsample_track, m)?)?;
    m.add_function(wrap_pyfunction!(find_matching_activities, m)?)?;
    Ok(())
}
