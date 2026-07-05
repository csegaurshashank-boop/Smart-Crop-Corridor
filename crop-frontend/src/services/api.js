import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`

  // Auto-attach current language to every request
  const lang = localStorage.getItem('i18nextLng') || 'en'
  const langCode = lang.startsWith('hi') ? 'hi' : 'en'
  if (!config.params) config.params = {}
  config.params.lang = langCode

  return config
})


// ================= AUTH =================

export const registerUser = (data) =>
  api.post('/auth/register', data)

export const loginUser = (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)

  return api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}

// ================= USERS =================

export const getMe = () =>
  api.get('/users/me')

export const listUsers = (role) =>
  api.get('/users/list', { params: role ? { role } : {} })

export const getUsersList = listUsers

export const createManager = (data) =>
  api.post('/users/create-manager', data)

// ================= FIELDS =================

// ================= FIELDS =================

export const registerField = (data) =>
  api.post('/fields/register', data)

export const listFields = (farmerId) =>
  api.get('/fields/list', {
    params: farmerId ? { farmer_id: farmerId } : {}
  })

export const getFields = listFields

export const getField = (fieldId) =>
  api.get(`/fields/${fieldId}`)

export const reanalyzeField = (fieldId) =>
  api.post(`/fields/analyze/${fieldId}`)

export const deleteField = (fieldId) =>
  api.delete(`/fields/${fieldId}`)

// ================= CORRIDORS =================

export const getCorridors = (fieldId) =>
  api.get(`/corridors/field/${fieldId}`)

export const updateNDVI = (data) =>
  api.put('/corridors/update-ndvi', data)


// ================= ANALYSIS =================

export const runNDVIAnalysis = (data) =>
  api.post('/analysis/ndvi', data)

export const getAnalysisStatus = (fieldId) =>
  api.get(`/analysis/status/${fieldId}`)

export const getAnalysisHistory = (fieldId) =>
  api.get(`/analysis/field/${fieldId}`)


// ================= ALERTS =================

export const getAlerts = (farmerId) =>
  api.get(`/alerts/farmer/${farmerId}`)

export const markAlertRead = (alertId) =>
  api.patch(`/alerts/${alertId}/read`)


// ================= MAP =================

export const getGeoJSON = (fieldId) =>
  api.get(`/map/geojson/${fieldId}`)

export const getNDVIHeatmap = (fieldId) =>
  api.get(`/visualization/ndvi/${fieldId}`)


// ================= RECOMMENDATIONS =================

export const getRecommendations = (fieldId) =>
  api.get(`/recommendations/field/${fieldId}`)

export const predictCrop = (data) =>
  api.post('/recommendations/predict-crop', data)

export const getFarmingGuide = (fieldId) =>
  api.get(`/recommendations/guide/${fieldId}`)


// ================= IRRIGATION =================

export const getIrrigationAlert = (fieldId) =>
  api.get(`/alerts/irrigation/${fieldId}`)


// ================= PEST ANALYSIS =================

export const runPestAnalysis = (fieldId, lang = 'en') =>
  api.post('/pest-analysis/run', { field_id: fieldId, lang })


export default api