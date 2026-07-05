import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Layers, Users, Map, TrendingUp, Plus, ChevronRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Sidebar from '../components/Sidebar'
import { listFields, listUsers } from '../services/api'

export default function ManagerDashboard() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [fields, setFields] = useState([])
  const [farmers, setFarmers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([listFields(), listUsers('farmer')]).then(([f, fm]) => {
      if (f.status === 'fulfilled') setFields(f.value.data || [])
      if (fm.status === 'fulfilled') setFarmers(fm.value.data || [])
      setLoading(false)
    })
  }, [])

  return (
    <div className="flex min-h-screen bg-earth-950">
      <Sidebar role="manager" />
      <main className="flex-1 ml-0 lg:ml-60 p-4 lg:p-8 pt-16 lg:pt-8">
        <div className="mb-10">
          <p className="text-earth-500 text-sm mb-1">{t('managerDash.overview')}</p>
          <h1 className="font-display text-3xl font-bold text-earth-50">{t('managerDash.title')}</h1>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
          {[
            { label: t('managerDash.totalFields'), value: fields.length, icon: <Layers size={20} />, bg: 'bg-crop-900/30', color: 'text-crop-400', border: 'border-crop-800/30', to: '/manager-dashboard/fields' },
            { label: t('managerDash.totalFarmers'), value: farmers.length, icon: <Users size={20} />, bg: 'bg-soil-900/30', color: 'text-soil-400', border: 'border-soil-800/30', to: '/manager-dashboard/farmers' },
            { label: t('managerDash.corridors'), value: fields.length * 25, icon: <Map size={20} />, bg: 'bg-blue-900/30', color: 'text-blue-400', border: 'border-blue-800/30', to: '/manager-dashboard/crop-guidance' },
            { label: t('managerDash.system'), value: t('managerDash.active'), icon: <TrendingUp size={20} />, bg: 'bg-emerald-900/30', color: 'text-emerald-400', border: 'border-emerald-800/30', to: null },
          ].map((s, i) => (
            <button key={i} onClick={() => s.to && navigate(s.to)}
              className={`${s.bg} border ${s.border} rounded-2xl p-5 text-left hover:scale-[1.02] transition-all duration-200`}>
              <div className={`${s.color} mb-3`}>{s.icon}</div>
              <div className="font-display text-2xl font-bold text-earth-100 mb-1">{loading ? '—' : s.value}</div>
              <div className="text-earth-500 text-xs font-body">{s.label}</div>
            </button>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mb-10">
          <h2 className="font-display text-xl font-semibold text-earth-200 mb-4">{t('managerDash.quickActions')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { title: t('managerDash.registerField'), desc: t('managerDash.registerFieldDesc'), icon: <Plus size={20} />, to: '/manager-dashboard/fields', color: 'text-crop-400' },
              { title: t('managerDash.viewCropMonitor'), desc: t('managerDash.viewCropMonitorDesc'), icon: <Map size={20} />, to: '/manager-dashboard/crop-guidance', color: 'text-blue-400' },
              { title: t('managerDash.manageFarmers'), desc: t('managerDash.manageFarmersDesc'), icon: <Users size={20} />, to: '/manager-dashboard/farmers', color: 'text-soil-400' },
            ].map((action, i) => (
              <button key={i} onClick={() => navigate(action.to)}
                className="glass-card rounded-xl p-5 text-left hover:border-earth-600 transition-all duration-200 group">
                <div className={`w-10 h-10 bg-earth-800 rounded-xl flex items-center justify-center mb-4 ${action.color}`}>{action.icon}</div>
                <h3 className="font-body font-semibold text-earth-100 mb-1">{action.title}</h3>
                <p className="text-earth-500 text-xs leading-relaxed mb-3">{action.desc}</p>
                <div className="flex items-center gap-1 text-earth-500 text-xs"><ChevronRight size={12} /></div>
              </button>
            ))}
          </div>
        </div>

        {/* Recent Fields */}
        {fields.length > 0 && (
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-lg font-semibold text-earth-100">{t('managerDash.recentFields')}</h3>
              <button onClick={() => navigate('/manager-dashboard/fields')} className="text-crop-400 text-xs hover:text-crop-300">
                {t('managerDash.viewAll')} →
              </button>
            </div>
            <div className="space-y-3">
              {fields.slice(0, 5).map((field) => (
                <div key={field.id} className="flex items-center justify-between p-3 bg-earth-900/40 rounded-xl border border-earth-800/30">
                  <div>
                    <div className="text-earth-300 text-sm font-body font-medium capitalize">{field.crop_type} Field</div>
                    <div className="text-earth-600 text-xs font-mono">{field.location?.lat?.toFixed(4)}, {field.location?.lng?.toFixed(4)} • {field.area} ha</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-earth-800 text-earth-400 px-2.5 py-1 rounded-full capitalize">{field.soil_type}</span>
                    <span className="text-xs bg-crop-900/40 text-crop-400 border border-crop-800/40 px-2.5 py-1 rounded-full">25 {t('managerDash.corridorsLabel')}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}