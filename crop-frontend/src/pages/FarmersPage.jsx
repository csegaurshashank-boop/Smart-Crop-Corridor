import React, { useEffect, useState } from 'react'
import { Users, Mail, Plus, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Sidebar from '../components/Sidebar'
import { listUsers, registerUser } from '../services/api'

export default function FarmersPage() {
  const { t } = useTranslation()
  const [farmers, setFarmers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [form, setForm] = useState({ name: '', email: '', password: '' })

  const load = async () => {
    setLoading(true)
    try {
      const res = await listUsers('farmer')
      setFarmers(res.data || [])
    } catch (e) {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await registerUser({ ...form, role: 'farmer' })
      setSuccess(t('farmers.successMsg'))
      setShowForm(false)
      setForm({ name: '', email: '', password: '' })
      await load()
      setTimeout(() => setSuccess(''), 4000)
    } catch (err) {
      setError(err.response?.data?.detail || t('common.failed'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen bg-earth-950">
      <Sidebar role="manager" />
      <main className="flex-1 ml-0 lg:ml-60 p-4 lg:p-8 pt-16 lg:pt-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <p className="text-earth-500 text-sm mb-1">{t('farmers.management')}</p>
            <h1 className="font-display text-3xl font-bold text-earth-50">{t('farmers.title')}</h1>
          </div>
          <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
            <Plus size={16} /> {t('farmers.registerBtn')}
          </button>
        </div>

        {success && <div className="bg-crop-900/30 border border-crop-800/50 rounded-xl px-4 py-3 text-crop-400 text-sm mb-6">✓ {success}</div>}

        {showForm && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6">
            <div className="glass-card rounded-2xl p-8 w-full max-w-md">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-display text-xl font-bold text-earth-100">{t('farmers.modalTitle')}</h2>
                <button onClick={() => setShowForm(false)}><X size={20} className="text-earth-500" /></button>
              </div>
              {error && <div className="bg-red-900/30 border border-red-800/50 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div><label className="label">{t('farmers.fullName')}</label><input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="input-field" placeholder={t('farmers.namePlaceholder')} required /></div>
                <div><label className="label">{t('farmers.email')}</label><input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} className="input-field" placeholder={t('farmers.emailPlaceholder')} required /></div>
                <div><label className="label">{t('farmers.password')}</label><input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} className="input-field" placeholder={t('farmers.minChars')} required minLength={6} /></div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setShowForm(false)} className="btn-secondary flex-1">{t('farmers.cancel')}</button>
                  <button type="submit" disabled={submitting} className="btn-primary flex-1 flex items-center justify-center">
                    {submitting ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : t('farmers.register')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20"><div className="w-8 h-8 border-2 border-crop-500 border-t-transparent rounded-full animate-spin" /></div>
        ) : farmers.length === 0 ? (
          <div className="glass-card rounded-2xl p-16 text-center">
            <Users size={40} className="text-earth-700 mx-auto mb-4" />
            <h3 className="font-display text-xl text-earth-600 mb-2">{t('farmers.noFarmers')}</h3>
            <button onClick={() => setShowForm(true)} className="btn-primary inline-flex items-center gap-2 mt-4"><Plus size={16} /> {t('farmers.registerFirst')}</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {farmers.map((farmer) => (
              <div key={farmer.id} className="glass-card rounded-2xl p-5 hover:border-earth-600 transition-all">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-earth-800 rounded-xl flex items-center justify-center">
                    <span className="text-earth-300 font-semibold text-sm">{farmer.name?.[0]?.toUpperCase() || farmer.email?.[0]?.toUpperCase()}</span>
                  </div>
                  <div>
                    <div className="text-earth-100 font-medium text-sm">{farmer.name || 'Unnamed'}</div>
                    <span className="text-xs bg-crop-900/40 text-crop-400 border border-crop-800/40 px-2 py-0.5 rounded-full">{t('login.farmer')}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-earth-500 text-xs"><Mail size={12} /> {farmer.email}</div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}