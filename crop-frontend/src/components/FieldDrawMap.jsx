 // src/components/FieldDrawMap.jsx
// Custom polygon drawing — no leaflet-draw plugin required.
// Uses only core Leaflet APIs so it always works with Vite + react-leaflet.

import { useEffect, useRef, useState, useCallback, memo } from "react";
import { MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { area as turfArea } from "@turf/area";
import { polygon as turfPolygon } from "@turf/helpers";

// Fix Vite asset missing marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:      "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const TILES = {
  satellite: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "© Esri World Imagery",
  },
  street: {
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
  },
};

// ─── cursor tracker & click handler ──────────────────────────────────────────
function DrawHandler({ drawing, onAddPoint, onFinish }) {
  useMapEvents({
    click(e) {
      if (!drawing) return;
      onAddPoint(e.latlng);
    },
    dblclick(e) {
      if (!drawing) return;
      e.originalEvent.preventDefault();   // stop zoom
      onFinish();
    },
  });
  return null;
}

// ─── internal controller: renders preview lines & finished polygon ─────────────
function MapController({ drawing, points, finishedPolygon, flyTo }) {
  const map = useMap();
  const previewLayersRef = useRef([]);
  const polygonLayerRef  = useRef(null);
  const dotLayersRef     = useRef([]);

  // fly-to
  useEffect(() => {
    if (flyTo) map.flyTo([flyTo.lat, flyTo.lng], flyTo.zoom || 15, { duration: 1.2 });
  }, [flyTo, map]);

  // cursor style
  useEffect(() => {
    const c = map.getContainer();
    c.style.cursor = drawing ? "crosshair" : "";
  }, [drawing, map]);

  // draw preview lines + dots while user is placing points
  useEffect(() => {
    // clear old preview
    previewLayersRef.current.forEach(l => { try { map.removeLayer(l); } catch(_){} });
    dotLayersRef.current.forEach(l => { try { map.removeLayer(l); } catch(_){} });
    previewLayersRef.current = [];
    dotLayersRef.current = [];

    if (!drawing || points.length === 0) return;

    // draw the dots at each point
    points.forEach((pt) => {
      const dot = L.circleMarker([pt.lat, pt.lng], {
        radius: 5, color: "#4ade80", fillColor: "#4ade80",
        fillOpacity: 1, weight: 2,
      }).addTo(map);
      dotLayersRef.current.push(dot);
    });

    // draw the current polyline
    if (points.length > 1) {
      const line = L.polyline(points.map(p => [p.lat, p.lng]), {
        color: "#4ade80", weight: 2, dashArray: "6 4",
      }).addTo(map);
      previewLayersRef.current.push(line);
    }

    // closing dashed line from last to first point
    if (points.length > 2) {
      const closingLine = L.polyline(
        [[points[points.length - 1].lat, points[points.length - 1].lng],
         [points[0].lat, points[0].lng]],
        { color: "#4ade80", weight: 1.5, dashArray: "4 6", opacity: 0.5 }
      ).addTo(map);
      previewLayersRef.current.push(closingLine);
    }
  }, [drawing, points, map]);

  // draw finished polygon
  useEffect(() => {
    if (polygonLayerRef.current) {
      try { map.removeLayer(polygonLayerRef.current); } catch(_) {}
      polygonLayerRef.current = null;
    }
    if (!finishedPolygon || finishedPolygon.length < 3) return;

    const poly = L.polygon(finishedPolygon.map(p => [p.lat, p.lng]), {
      color: "#4ade80", fillColor: "#22c55e",
      fillOpacity: 0.2, weight: 2,
    }).addTo(map);
    polygonLayerRef.current = poly;
  }, [finishedPolygon, map]);

  return null;
}

// ─── GPS / Search pin marker ───────────────────────────────────────────────────
// Renders a single Leaflet marker that updates whenever `position` changes.
// Keeping this as a separate inner component lets us use useMap() cleanly.
function GpsMarkerLayer({ position }) {
  const map = useMap();
  const markerRef = useRef(null);

  useEffect(() => {
    // Remove previous marker
    if (markerRef.current) {
      try { map.removeLayer(markerRef.current); } catch (_) {}
      markerRef.current = null;
    }
    if (!position) return;

    // Create a slightly larger, highlighted marker icon for the GPS pin
    const icon = L.divIcon({
      className: "",
      html: `<div style="
        width:22px;height:22px;background:#4ade80;border:3px solid #fff;
        border-radius:50% 50% 50% 0;transform:rotate(-45deg);
        box-shadow:0 2px 8px rgba(0,0,0,0.5);
      "></div>`,
      iconSize:   [22, 22],
      iconAnchor: [11, 22],
      popupAnchor:[0, -22],
    });

    markerRef.current = L.marker([position.lat, position.lng], { icon })
      .addTo(map)
      .bindPopup(`📍 ${position.lat.toFixed(5)}, ${position.lng.toFixed(5)}`);
  }, [position, map]);

  return null;
}

// ─── main component ───────────────────────────────────────────────────────────
// Wrapped in memo — only re-renders when onPolygonDrawn / onLocationDetected /
// initialCenter / initialZoom props change (parent uses useCallback for handlers).
function FieldDrawMapBase({
  onPolygonDrawn,
  onLocationDetected,
  initialCenter = [25.43, 81.84],
  initialZoom   = 13,
}) {
  const [tileLayer,     setTileLayer]     = useState("satellite");
  const [drawing,       setDrawing]       = useState(false);
  const [points,        setPoints]        = useState([]);          // live points
  const [finishedPoly,  setFinishedPoly]  = useState(null);       // completed polygon
  const [areaHa,        setAreaHa]        = useState(null);
  const [searchQuery,   setSearchQuery]   = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [flyTo,         setFlyTo]         = useState(null);
  const [gpsLoading,    setGpsLoading]    = useState(false);
  const [gpsMarker,     setGpsMarker]     = useState(null);       // {lat, lng} for pin
  const [searchLoading, setSearchLoading] = useState(false);      // search button spinner
  const [searchError,   setSearchError]   = useState("");         // "Location not found"
  const searchTimeout = useRef(null);

  // ── compute area and fire callback when polygon is finished ──────────────────
  const finishPolygon = useCallback(() => {
    if (points.length < 3) return;

    const closedPoints = [...points, points[0]];
    const coords = [closedPoints.map(p => [p.lng, p.lat])]; // GeoJSON [lng, lat]

    let ha = 0;
    try {
      ha = parseFloat((turfArea(turfPolygon(coords)) / 10000).toFixed(4));
    } catch (_) {}

    setAreaHa(ha);
    setFinishedPoly(points);
    setPoints([]);
    setDrawing(false);

    const avgLat = points.reduce((s, p) => s + p.lat, 0) / points.length;
    const avgLng = points.reduce((s, p) => s + p.lng, 0) / points.length;

    onPolygonDrawn?.(
      { type: "Polygon", coordinates: coords },
      ha,
      { lat: avgLat, lng: avgLng }
    );
  }, [points, onPolygonDrawn]);

  const startDrawing = () => {
    setPoints([]);
    setFinishedPoly(null);
    setAreaHa(null);
    setDrawing(true);
    onPolygonDrawn?.(null, 0, null);
  };

  const clearAll = () => {
    setPoints([]);
    setFinishedPoly(null);
    setAreaHa(null);
    setDrawing(false);
    onPolygonDrawn?.(null, 0, null);
  };

  const addPoint = useCallback((latlng) => {
    setPoints(prev => [...prev, latlng]);
  }, []);

  // ── search ────────────────────────────────────────────────────────────────────
  const handleSearch = (val) => {
    setSearchQuery(val);
    clearTimeout(searchTimeout.current);
    if (val.length < 3) { setSearchResults([]); return; }
    searchTimeout.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(val)}&format=json&limit=5`,
          { headers: { "Accept-Language": "en" } }
        );
        setSearchResults(await res.json());
      } catch (_) { setSearchResults([]); }
    }, 500);
  };

  const selectResult = (r) => {
    const lat = parseFloat(r.lat), lng = parseFloat(r.lon);
    setFlyTo({ lat, lng, zoom: 15 });
    setGpsMarker({ lat, lng });
    setSearchQuery(r.display_name.split(",")[0]);
    setSearchResults([]);
    setSearchError("");
    onLocationDetected?.(lat, lng);
  };

  // ── Search button handler ─────────────────────────────────────────────────────
  const handleSearchButton = async () => {
    const q = searchQuery.trim();
    if (!q) return;
    setSearchLoading(true);
    setSearchError("");
    setSearchResults([]);
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=1`,
        { headers: { "Accept-Language": "en" } }
      );
      const data = await res.json();
      if (data && data.length > 0) {
        const lat = parseFloat(data[0].lat);
        const lng = parseFloat(data[0].lon);
        setFlyTo({ lat, lng, zoom: 15 });
        setGpsMarker({ lat, lng });
        setSearchQuery(data[0].display_name.split(",")[0]);
        onLocationDetected?.(lat, lng);
      } else {
        setSearchError("Location not found");
      }
    } catch (_) {
      setSearchError("Location not found");
    } finally {
      setSearchLoading(false);
    }
  };

  // ── GPS ───────────────────────────────────────────────────────────────────────
  const detectGPS = () => {
    if (!navigator.geolocation) return;
    setGpsLoading(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const lat = coords.latitude, lng = coords.longitude;
        setFlyTo({ lat, lng, zoom: 16 });
        setGpsMarker({ lat, lng });
        onLocationDetected?.(lat, lng);
        setGpsLoading(false);
      },
      () => setGpsLoading(false),
      { timeout: 8000 }
    );
  };

  // ── render ────────────────────────────────────────────────────────────────────
  return (
    <div className="relative w-full h-full flex flex-col gap-2">

      {/* ── search row ── */}
      <div className="relative z-[1000] flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => { handleSearch(e.target.value); setSearchError(""); }}
            onKeyDown={(e) => e.key === "Enter" && handleSearchButton()}
            placeholder="Search village, city or address…"
            className="w-full bg-earth-800 border border-earth-700 text-earth-100
                       rounded-lg px-4 py-2.5 text-sm placeholder-earth-500
                       focus:outline-none focus:border-crop-500 transition"
          />
          {searchResults.length > 0 && (
            <ul className="absolute top-full mt-1 w-full bg-earth-900 border border-earth-700
                           rounded-lg shadow-2xl max-h-48 overflow-y-auto z-50">
              {searchResults.map((r) => (
                <li key={r.place_id} onClick={() => selectResult(r)}
                  className="px-4 py-2.5 text-sm text-earth-200 hover:bg-earth-800
                             cursor-pointer border-b border-earth-800 last:border-0 truncate">
                  {r.display_name}
                </li>
              ))}
            </ul>
          )}
          {/* search error tooltip */}
          {searchError && (
            <p className="absolute top-full mt-1 left-0 text-xs text-red-400 bg-red-950/80
                          border border-red-900/50 rounded-md px-3 py-1.5 z-50 whitespace-nowrap">
              ⚠ {searchError}
            </p>
          )}
        </div>

        {/* Search button */}
        <button type="button" onClick={handleSearchButton}
          disabled={!searchQuery.trim() || searchLoading}
          title="Search this location"
          className="px-3 py-2.5 bg-crop-700 hover:bg-crop-600 border border-crop-600
                     rounded-lg text-white transition disabled:opacity-50
                     flex items-center gap-1.5 text-xs font-semibold"
        >
          {searchLoading
            ? <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
            : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="11" cy="11" r="8" strokeWidth="2"/>
                <path d="M21 21l-4.35-4.35" strokeWidth="2" strokeLinecap="round"/>
              </svg>}
          {searchLoading ? "" : "Search"}
        </button>

        {/* GPS */}
        <button type="button" onClick={detectGPS} disabled={gpsLoading}
          title="Use current GPS location"
          className="px-3 py-2.5 bg-earth-800 border border-earth-700 rounded-lg
                     text-earth-300 hover:border-crop-500 hover:text-crop-400
                     transition disabled:opacity-50 flex items-center gap-1.5 text-xs font-semibold">
          {gpsLoading
            ? <div className="w-4 h-4 border-2 border-crop-500 border-t-transparent rounded-full animate-spin" />
            : <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="3" strokeWidth="2"/>
                <path d="M12 2v3M12 19v3M2 12h3M19 12h3" strokeWidth="2" strokeLinecap="round"/>
              </svg>GPS</>}
        </button>

        {/* tile toggle */}
        <button type="button"
          onClick={() => setTileLayer(t => t === "street" ? "satellite" : "street")}
          className="px-3 py-2.5 bg-earth-800 border border-earth-700 rounded-lg
                     text-earth-300 hover:border-crop-500 hover:text-crop-400 transition text-xs font-semibold">
          {tileLayer === "street" ? "🛰 SAT" : "🗺 MAP"}
        </button>
      </div>

      {/* ── draw control bar ── */}
      <div className="flex items-center gap-2 z-[1000]">
        {!drawing && !finishedPoly && (
          <button type="button" onClick={startDrawing}
            className="flex items-center gap-2 px-4 py-2 bg-crop-700 hover:bg-crop-600
                       text-white text-sm font-semibold rounded-lg transition-all duration-150
                       shadow-lg ring-1 ring-crop-500/40">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Draw Field Boundary
          </button>
        )}

        {drawing && (
          <>
            <div className="flex items-center gap-2 px-3 py-2 bg-crop-900/60 border border-crop-700
                            rounded-lg text-crop-300 text-xs font-medium animate-pulse">
              <span className="w-2 h-2 bg-crop-400 rounded-full inline-block" />
              {points.length === 0
                ? "Click on the map to place points"
                : points.length < 3
                ? `${points.length} point${points.length > 1 ? "s" : ""} — need at least 3`
                : `${points.length} points — double-click to finish`}
            </div>

            {points.length >= 3 && (
              <button type="button" onClick={finishPolygon}
                className="px-3 py-2 bg-crop-600 hover:bg-crop-500 text-white
                           text-xs font-semibold rounded-lg transition">
                ✓ Finish
              </button>
            )}
            <button type="button" onClick={clearAll}
              className="px-3 py-2 bg-earth-800 hover:bg-earth-700 text-earth-300
                         text-xs font-semibold rounded-lg transition">
              Cancel
            </button>
          </>
        )}

        {finishedPoly && (
          <>
            <div className="flex items-center gap-2 px-3 py-2 bg-crop-900/40 border border-crop-800/60 rounded-lg">
              <span className="text-crop-400 text-sm">✓</span>
              <span className="text-crop-300 text-xs font-medium">
                Field drawn · <strong>{areaHa} ha</strong>
              </span>
            </div>
            <button type="button" onClick={startDrawing}
              className="px-3 py-2 bg-earth-800 hover:bg-earth-700 text-earth-300
                         text-xs font-semibold rounded-lg transition">
              Redraw
            </button>
          </>
        )}
      </div>

      {/* ── map ── */}
      <div className="flex-1 rounded-xl overflow-hidden border border-earth-700 min-h-[300px]">
        <MapContainer center={initialCenter} zoom={initialZoom}
          style={{ height: "100%", width: "100%" }} doubleClickZoom={false}>
          <TileLayer key={tileLayer} url={TILES[tileLayer].url}
            attribution={TILES[tileLayer].attribution} maxZoom={21} />
          <MapController drawing={drawing} points={points}
            finishedPolygon={finishedPoly} flyTo={flyTo} />
          <DrawHandler drawing={drawing} onAddPoint={addPoint} onFinish={finishPolygon} />
          <GpsMarkerLayer position={gpsMarker} />
        </MapContainer>
      </div>
    </div>
  );
}

export default memo(FieldDrawMapBase);