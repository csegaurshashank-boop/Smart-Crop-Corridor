import React, { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'

// ── Lazy-loaded pages (split into separate chunks, loaded only when visited) ──
const LandingPage        = lazy(() => import('./pages/LandingPage'))
const RegisterPage       = lazy(() => import('./pages/RegisterPage'))
const LoginPage          = lazy(() => import('./pages/LoginPage'))
const FarmerDashboard    = lazy(() => import('./pages/FarmerDashboard'))
const ManagerDashboard   = lazy(() => import('./pages/ManagerDashboard'))
const CropGuidancePage   = lazy(() => import('./pages/CropGuidancePage'))
const PestDetectionPage  = lazy(() => import('./pages/PestDetectionPage'))
const FieldsPage         = lazy(() => import('./pages/FieldsPage'))
const FarmersPage        = lazy(() => import('./pages/FarmersPage'))
// ImagePestDetectionPage kept in file system but not active in routing

// ── Shared loading fallback ───────────────────────────────────────────────────
function PageLoader() {
  return (
    <div className="min-h-screen bg-earth-950 flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="w-9 h-9 border-2 border-crop-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-earth-500 text-sm">Loading…</p>
      </div>
    </div>
  )
}

function ProtectedRoute({ children, requiredRole }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="min-h-screen bg-earth-950 flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-crop-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
  if (!user) return <Navigate to="/login" replace />
  if (requiredRole && user.role !== requiredRole) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<LoginPage />} />

          <Route path="/dashboard" element={
            <ProtectedRoute requiredRole="farmer"><FarmerDashboard /></ProtectedRoute>
          } />
          <Route path="/dashboard/crop-guidance" element={
            <ProtectedRoute requiredRole="farmer"><CropGuidancePage /></ProtectedRoute>
          } />
          <Route path="/dashboard/pest-detection" element={
            <ProtectedRoute requiredRole="farmer"><PestDetectionPage /></ProtectedRoute>
          } />
          {/* /dashboard/pest-image — removed from UI; redirect to dashboard safely */}
          <Route path="/dashboard/pest-image" element={<Navigate to="/dashboard" replace />} />

          <Route path="/manager-dashboard" element={
            <ProtectedRoute><ManagerDashboard /></ProtectedRoute>
          } />
          <Route path="/manager-dashboard/fields" element={
            <ProtectedRoute><FieldsPage /></ProtectedRoute>
          } />
          <Route path="/manager-dashboard/farmers" element={
            <ProtectedRoute><FarmersPage /></ProtectedRoute>
          } />
          <Route path="/manager-dashboard/crop-guidance" element={
            <ProtectedRoute><CropGuidancePage /></ProtectedRoute>
          } />
          <Route path="/manager-dashboard/pest-detection" element={
            <ProtectedRoute><PestDetectionPage /></ProtectedRoute>
          } />
          {/* /manager-dashboard/pest-image — removed from UI; redirect to manager dashboard safely */}
          <Route path="/manager-dashboard/pest-image" element={<Navigate to="/manager-dashboard" replace />} />

          <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  )
}