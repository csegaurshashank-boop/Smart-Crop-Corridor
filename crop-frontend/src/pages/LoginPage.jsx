import React, { useState } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { Leaf, User, Briefcase, Eye, EyeOff, ArrowRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { loginUser } from '../services/api'
import { useAuth } from '../context/AuthContext'
import LanguageSwitcher from '../components/LanguageSwitcher'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()
  const { t } = useTranslation()
  const [role, setRole] = useState('farmer')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ email: '', password: '' })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await loginUser(form.email, form.password)
      const { access_token, role: userRole, user_id } = res.data
      login(access_token, { role: userRole, user_id, email: form.email })
      navigate(userRole === 'farmer' ? '/dashboard' : '/manager-dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || t('login.invalidError'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-earth-950 relative overflow-hidden flex items-center justify-center p-6">
      <div className="absolute inset-0 bg-field-pattern opacity-20" />
      <div className="absolute top-4 right-6 z-20"><LanguageSwitcher /></div>

      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-8 h-8 bg-crop-600 rounded-lg flex items-center justify-center">
              <Leaf size={16} className="text-white" />
            </div>
            <span className="font-display font-semibold text-earth-100">CropCorridor</span>
          </Link>
          <h1 className="font-display text-3xl font-bold text-earth-50 mb-2">{t('login.title')}</h1>
          <p className="text-earth-500 text-sm">{t('login.subtitle')}</p>
        </div>

        {location.state?.registered && (
          <div className="bg-crop-900/30 border border-crop-800/50 rounded-xl px-4 py-3 text-crop-400 text-sm mb-4 text-center">
            ✓ {t('login.successMsg')}
          </div>
        )}

        <div className="glass-card rounded-2xl p-8">
          <div className="flex bg-earth-900 rounded-xl p-1 mb-6">
            {['farmer', 'manager'].map((r) => (
              <button key={r} onClick={() => setRole(r)}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-body font-medium transition-all duration-200 ${
                  role === r ? 'bg-earth-700 text-earth-100' : 'text-earth-500 hover:text-earth-300'
                }`}>
                {r === 'farmer' ? <User size={14} /> : <Briefcase size={14} />}
                {r === 'farmer' ? t('login.farmer') : t('login.manager')}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && <div className="bg-red-900/30 border border-red-800/50 rounded-xl px-4 py-3 text-red-400 text-sm">{error}</div>}
            <div>
              <label className="label">{t('login.email')}</label>
              <input type="email" value={form.email}
                onChange={e => { setForm({ ...form, email: e.target.value }); setError('') }}
                className="input-field" placeholder={t('login.emailPlaceholder')} required />
            </div>
            <div>
              <label className="label">{t('login.password')}</label>
              <div className="relative">
                <input type={showPass ? 'text' : 'password'} value={form.password}
                  onChange={e => { setForm({ ...form, password: e.target.value }); setError('') }}
                  className="input-field pr-10" placeholder={t('login.passwordPlaceholder')} required />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-earth-500">
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 mt-2">
              {loading
                ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                : <><ArrowRight size={16} /> {t('login.signInAs')} {role === 'farmer' ? t('login.farmer') : t('login.manager')}</>}
            </button>
          </form>

          <div className="text-center mt-4">
            <span className="text-earth-500 text-sm">{t('login.noAccount')} </span>
            <Link to="/register" className="text-crop-400 text-sm font-medium">{t('login.register')}</Link>
          </div>
        </div>
      </div>
    </div>
  )
}