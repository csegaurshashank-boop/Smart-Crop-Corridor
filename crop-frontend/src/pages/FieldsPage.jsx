// src/pages/FieldsPage.jsx
// Manager page — register fields (AI-driven, no crop/soil inputs)

import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  MapPin, Plus, X, ChevronRight, Layers, Trash2,
  Activity, CheckCircle2, AlertCircle, Clock,
} from "lucide-react";
import FieldDrawMap from "../components/FieldDrawMap";
import LandAnalysisCard from "../components/LandAnalysisCard";
import Sidebar from "../components/Sidebar";
import { registerField, getFields, getUsersList, deleteField } from "../services/api";

// ── status badge ──────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const map = {
    pending:   { label: "Pending",   cls: "bg-earth-800 text-earth-400",      Icon: Clock },
    running:   { label: "Analysing", cls: "bg-yellow-900/40 text-yellow-400", Icon: Activity },
    completed: { label: "Completed", cls: "bg-crop-900/40 text-crop-400",     Icon: CheckCircle2 },
    failed:    { label: "Failed",    cls: "bg-red-900/40 text-red-400",        Icon: AlertCircle },
  };
  const { label, cls, Icon } = map[status] || map.pending;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      <Icon className="w-3 h-3" /> {label}
    </span>
  );
}

// ── ndvi health dot ───────────────────────────────────────────────────────────
function NdviTag({ value }) {
  if (!value && value !== 0) return null;
  const color = value > 0.6 ? "bg-green-500" : value >= 0.3 ? "bg-yellow-500" : "bg-red-500";
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-earth-400">
      <span className={`w-2 h-2 rounded-full ${color}`} />
      NDVI {value.toFixed(2)}
    </span>
  );
}

// ── main component ────────────────────────────────────────────────────────────
export default function FieldsPage() {
  const { t } = useTranslation();

  const [fields,   setFields]   = useState([]);
  const [farmers,  setFarmers]  = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [modalOpen, setModal]   = useState(false);
  const [selected, setSelected] = useState(null); // field clicked for detail
  const [saving,   setSaving]   = useState(false);
  const [error,    setError]    = useState("");

  // form state
  const [form, setForm] = useState({
    farmer_id: "",
    lat: "",
    lng: "",
    area: "",
    boundary: null,
  });

  // ── load data ──────────────────────────────────────────────────────────────
  useEffect(() => {
    loadPage();
  }, []);

  // live-poll running fields
  useEffect(() => {
    const hasRunning = fields.some((f) =>
      f.analysis_status === "running" || f.analysis_status === "pending"
    );
    if (!hasRunning) return;
    const id = setInterval(loadFields, 3000);
    return () => clearInterval(id);
  }, [fields]);

  async function loadPage() {
    await Promise.all([loadFields(), loadFarmers()]);
    setLoading(false);
  }

  async function loadFields() {
    try {
      const res = await getFields();
      // backend returns a plain list, not { fields: [...] }
      setFields(Array.isArray(res.data) ? res.data : res.data?.fields || []);
    } catch (_) {}
  }

  async function loadFarmers() {
    try {
      const res = await getUsersList("farmer");
      // backend returns a plain list
      setFarmers(Array.isArray(res.data) ? res.data : res.data?.users || []);
    } catch (_) {}
  }

  // ── map callbacks ──────────────────────────────────────────────────────────
  const handlePolygonDrawn = useCallback((geojson, areaHa, center) => {
    setForm((f) => ({
      ...f,
      boundary: geojson,
      area:     areaHa > 0 ? areaHa.toString() : f.area,
      lat:      center ? center.lat.toFixed(6) : f.lat,
      lng:      center ? center.lng.toFixed(6) : f.lng,
    }));
  }, []);

  const handleLocationDetected = useCallback((lat, lng) => {
    setForm((f) => ({
      ...f,
      lat: lat.toFixed(6),
      lng: lng.toFixed(6),
    }));
  }, []);

  // ── register field ─────────────────────────────────────────────────────────
  async function handleRegister(e) {
    e.preventDefault();
    if (!form.farmer_id)             return setError("Please assign a farmer.");
    if (!form.lat || !form.lng)      return setError("Latitude & longitude are required.");
    if (!form.area || form.area <= 0) return setError("Area must be greater than 0.");
    setError("");
    setSaving(true);
    try {
      await registerField({
        farmer_id: form.farmer_id,
        lat:       parseFloat(form.lat),
        lng:       parseFloat(form.lng),
        area:      parseFloat(form.area),
        boundary:  form.boundary,
      });
      setModal(false);
      resetForm();
      await loadFields();
    } catch (err) {
      setError(err?.response?.data?.detail || "Registration failed.");
    } finally {
      setSaving(false);
    }
  }

  function resetForm() {
    setForm({ farmer_id: "", lat: "", lng: "", area: "", boundary: null });
    setError("");
  }

  // ── delete field ───────────────────────────────────────────────────────────
  async function handleDelete(e, fieldId) {
    e.stopPropagation(); // don't expand the card
    if (!window.confirm("Are you sure you want to delete this field? This action cannot be undone.")) return;
    try {
      await deleteField(fieldId);
      setFields((prev) => prev.filter((f) => f.id !== fieldId));
      if (selected?.id === fieldId) setSelected(null);
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to delete field.");
    }
  }

  const farmerName = (id) => {
    const f = farmers.find((x) => x.id === id || x.user_id === id);
    return f ? f.name || f.email : id;
  };

  // ── render ─────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex min-h-screen bg-earth-950">
        <Sidebar role="manager" />
        <main className="flex-1 ml-0 lg:ml-60 p-4 lg:p-8 pt-16 lg:pt-8 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-crop-500 border-t-transparent rounded-full animate-spin" />
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-earth-950">
      <Sidebar role="manager" />
      <main className="flex-1 ml-0 lg:ml-60 p-4 lg:p-8 pt-16 lg:pt-8">
      <div className="space-y-6">
      {/* header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-earth-100">Field Registry</h1>
          <p className="text-sm text-earth-500 mt-0.5">
            {fields.length} field{fields.length !== 1 ? "s" : ""} registered · AI-powered analysis
          </p>
        </div>
        <button onClick={() => setModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Register Field
        </button>
      </div>

      {/* field cards grid */}
      {fields.length === 0 ? (
        <div className="glass-card p-12 text-center space-y-3">
          <MapPin className="w-10 h-10 text-earth-600 mx-auto" />
          <p className="text-earth-400 font-medium">No fields registered yet</p>
          <p className="text-sm text-earth-600">Register a field to start AI land analysis</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {fields.map((field) => (
            <div
              key={field.id}
              onClick={() => setSelected(selected?.id === field.id ? null : field)}
              className={`glass-card p-5 cursor-pointer transition-all duration-200
                hover:border-earth-600 space-y-4
                ${selected?.id === field.id ? "border-crop-700 ring-1 ring-crop-700/30" : ""}`}
            >
              {/* card header */}
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-3.5 h-3.5 text-crop-500 flex-shrink-0" />
                    <p className="text-sm font-semibold text-earth-200 truncate">
                      {farmerName(field.farmer_id)}
                    </p>
                  </div>
                  <p className="text-xs text-earth-500 font-mono pl-5">
                    {(field.location?.lat ?? field.center?.lat)?.toFixed(4)}, {(field.location?.lng ?? field.center?.lng)?.toFixed(4)}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={field.analysis_status} />
                    <button
                      onClick={(e) => handleDelete(e, field.id)}
                      title="Delete field"
                      className="p-1.5 rounded-md text-red-500 bg-red-900/20
                                 hover:text-red-300 hover:bg-red-900/40
                                 transition-colors duration-150 flex-shrink-0"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  {field.land_analysis?.ndvi_avg != null && (
                    <NdviTag value={field.land_analysis.ndvi_avg} />
                  )}
                </div>
              </div>

              {/* area */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-earth-500">Area</span>
                <span className="text-earth-300 font-mono">{field.area} ha</span>
              </div>

              {/* crop recommendation preview */}
              {field.analysis_status === "completed" && field.recommended_crop && (
                <div className="pt-3 border-t border-earth-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-earth-500">Recommended Crop</span>
                    <span className="text-sm font-semibold text-crop-300 capitalize">
                      {field.recommended_crop}
                    </span>
                  </div>
                  <div className="w-full bg-earth-800 rounded-full h-1.5">
                    <div
                      className="h-1.5 rounded-full bg-gradient-to-r from-crop-700 to-crop-400"
                      style={{ width: `${field.crop_confidence || 0}%` }}
                    />
                  </div>
                  {field.alternative_crops?.length > 0 && (
                    <div className="flex gap-1.5 flex-wrap">
                      {field.alternative_crops.map((c) => (
                        <span key={c}
                          className="px-2 py-0.5 bg-earth-800 rounded-full text-xs text-earth-400 capitalize">
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* expand caret */}
              <div className="flex justify-end">
                <ChevronRight
                  className={`w-4 h-4 text-earth-600 transition-transform duration-200
                    ${selected?.id === field.id ? "rotate-90" : ""}`}
                />
              </div>

              {/* inline analysis card */}
              {selected?.id === field.id && (
                <div className="pt-3 border-t border-earth-800">
                  <LandAnalysisCard
                    field={field}
                    onAnalysisComplete={(d) => {
                      setFields((prev) =>
                        prev.map((f) => f.id === field.id ? { ...f, ...d } : f)
                      );
                    }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── registration modal ── */}
      {modalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center
                     bg-black/70 backdrop-blur-sm overflow-y-auto py-8 px-4"
          onClick={(e) => e.target === e.currentTarget && (setModal(false), resetForm())}
        >
          <div className="w-full max-w-3xl bg-earth-950 border border-earth-800 rounded-2xl
                          shadow-2xl overflow-hidden">
            {/* modal header */}
            <div className="flex items-center justify-between px-6 py-5
                            border-b border-earth-800">
              <div>
                <h2 className="text-lg font-display font-bold text-earth-100">Register Field</h2>
                <p className="text-xs text-earth-500 mt-0.5">
                  AI will automatically analyze land & recommend the best crop
                </p>
              </div>
              <button
                onClick={() => { setModal(false); resetForm(); }}
                className="p-1.5 rounded-lg text-earth-500 hover:text-earth-300
                           hover:bg-earth-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRegister} className="p-6 space-y-6">
              {/* AI notice */}
              <div className="flex gap-3 p-4 bg-crop-950/40 border border-crop-900/50 rounded-xl">
                <Layers className="w-5 h-5 text-crop-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="text-crop-300 font-semibold mb-0.5">AI-Driven Analysis</p>
                  <p className="text-earth-400 text-xs leading-relaxed">
                    You don't need to enter crop or soil type. After registration the system
                    will automatically simulate soil conditions, calculate NDVI across 25 corridors,
                    and predict the best crop using the ML model.
                  </p>
                </div>
              </div>

              {/* assign farmer */}
              <div>
                <label className="label">Assign Farmer *</label>
                <select
                  required
                  value={form.farmer_id}
                  onChange={(e) => setForm({ ...form, farmer_id: e.target.value })}
                  className="input-field w-full mt-1"
                >
                  <option value="">Select a farmer…</option>
                  {farmers.map((f) => (
                    <option key={f.id || f.user_id} value={f.id || f.user_id}>
                      {f.name || f.email}
                    </option>
                  ))}
                </select>
              </div>

              {/* map */}
              <div>
                <label className="label mb-2 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5" /> Field Location & Boundary
                </label>
                <div className="h-[380px]">
                  <FieldDrawMap
                    onPolygonDrawn={handlePolygonDrawn}
                    onLocationDetected={handleLocationDetected}
                    initialCenter={[25.43, 81.84]}
                    initialZoom={13}
                  />
                </div>
              </div>

              {/* lat / lng / area */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="label">Latitude *</label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="25.430000"
                    value={form.lat}
                    onChange={(e) => setForm({ ...form, lat: e.target.value })}
                    className="input-field w-full mt-1 font-mono text-sm"
                  />
                </div>
                <div>
                  <label className="label">Longitude *</label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="81.840000"
                    value={form.lng}
                    onChange={(e) => setForm({ ...form, lng: e.target.value })}
                    className="input-field w-full mt-1 font-mono text-sm"
                  />
                </div>
                <div>
                  <label className="label">Area (hectares)</label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0.0001"
                    placeholder="auto-calculated"
                    value={form.area}
                    onChange={(e) => setForm({ ...form, area: e.target.value })}
                    className="input-field w-full mt-1 font-mono text-sm"
                  />
                  {form.boundary && (
                    <p className="text-xs text-crop-500 mt-1">✓ Auto-filled from polygon</p>
                  )}
                </div>
              </div>

              {/* error */}
              {error && (
                <div className="flex gap-2 text-sm text-red-400 bg-red-900/20
                                border border-red-900/40 rounded-lg px-4 py-3">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  {error}
                </div>
              )}

              {/* actions */}
              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => { setModal(false); resetForm(); }}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="btn-primary flex items-center gap-2 min-w-[200px] justify-center"
                >
                  {saving ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white
                                      rounded-full animate-spin" />
                      Registering…
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4" /> Register & Start AI Analysis
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      </div>
      </main>
    </div>
  );
}