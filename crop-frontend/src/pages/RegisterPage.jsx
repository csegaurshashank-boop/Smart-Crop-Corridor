import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Leaf, User, Briefcase, ArrowRight, ArrowLeft, Eye, EyeOff } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { registerUser } from '../services/api'
import LanguageSwitcher from '../components/LanguageSwitcher'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [step, setStep] = useState(1)
  const [role, setRole] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ name: '', email: '', password: '', phone: '', address: '', organization: '' })

  const handleChange = (e) => { setForm({ ...form, [e.target.name]: e.target.value }); setError('') }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await registerUser({ name: form.name, email: form.email, password: form.password, role })
      navigate('/login', { state: { registered: true } })
    } catch (err) {
      setError(err.response?.data?.detail || t('common.failed'))
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
          <h1 className="font-display text-3xl font-bold text-earth-50 mb-2">
            {step === 1 ? t('register.title1') : role === 'farmer' ? t('register.title2') : t('register.title3')}
          </h1>
          <p className="text-earth-500 text-sm">
            {step === 1 ? t('register.chooseRole') : t('register.fillDetails')}
          </p>
        </div>

        <div className="glass-card rounded-2xl p-8">
          {step === 1 ? (
            <div className="space-y-4">
              {[
                { r: 'farmer', icon: <User size={22} className="text-crop-400" />, title: t('register.farmerTitle'), desc: t('register.farmerDesc'), border: 'hover:border-crop-600' },
                { r: 'manager', icon: <Briefcase size={22} className="text-soil-400" />, title: t('register.managerTitle'), desc: t('register.managerDesc'), border: 'hover:border-soil-500' },
              ].map(({ r, icon, title, desc, border }) => (
                <button key={r} onClick={() => { setRole(r); setStep(2) }}
                  className={`w-full p-5 rounded-xl border border-earth-700 ${border} bg-earth-900/50 transition-all duration-200 text-left group`}>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-earth-800 rounded-xl flex items-center justify-center">{icon}</div>
                    <div>
                      <div className="font-body font-semibold text-earth-100 mb-1">{title}</div>
                      <div className="text-earth-500 text-xs">{desc}</div>
                    </div>
                    <ArrowRight size={16} className="text-earth-600 ml-auto" />
                  </div>
                </button>
              ))}
              <div className="text-center pt-2">
                <span className="text-earth-500 text-sm">{t('register.alreadyAccount')} </span>
                <Link to="/login" className="text-crop-400 text-sm font-medium">{t('register.signIn')}</Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <button type="button" onClick={() => setStep(1)}
                className="flex items-center gap-1 text-earth-500 hover:text-earth-300 text-sm mb-2">
                <ArrowLeft size={14} /> {t('register.back')}
              </button>
              {error && <div className="bg-red-900/30 border border-red-800/50 rounded-xl px-4 py-3 text-red-400 text-sm">{error}</div>}
              <div>
                <label className="label">{t('register.fullName')}</label>
                <input name="name" value={form.name} onChange={handleChange} className="input-field" placeholder={t('register.namePlaceholder')} required />
              </div>
              <div>
                <label className="label">{t('register.email')}</label>
                <input name="email" type="email" value={form.email} onChange={handleChange} className="input-field" placeholder={t('register.emailPlaceholder')} required />
              </div>
              <div>
                <label className="label">{t('register.password')}</label>
                <div className="relative">
                  <input name="password" type={showPass ? 'text' : 'password'} value={form.password} onChange={handleChange}
                    className="input-field pr-10" placeholder={t('register.minChars')} required minLength={6} />
                  <button type="button" onClick={() => setShowPass(!showPass)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-earth-500">
                    {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              {role === 'farmer' && (
                <>
                  <div><label className="label">{t('register.phone')}</label><input name="phone" value={form.phone} onChange={handleChange} className="input-field" placeholder={t('register.phonePlaceholder')} /></div>
                  <div><label className="label">{t('register.address')}</label><input name="address" value={form.address} onChange={handleChange} className="input-field" placeholder={t('register.addressPlaceholder')} /></div>
                </>
              )}
              {role === 'manager' && (
                <>
                  <div><label className="label">{t('register.organization')}</label><input name="organization" value={form.organization} onChange={handleChange} className="input-field" placeholder={t('register.orgPlaceholder')} /></div>
                  <div><label className="label">{t('register.phone')}</label><input name="phone" value={form.phone} onChange={handleChange} className="input-field" placeholder={t('register.phonePlaceholder')} /></div>
                </>
              )}
              <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 mt-2">
                {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><ArrowRight size={16} />{t('register.createAccount')}</>}
              </button>
              <div className="text-center">
                <span className="text-earth-500 text-sm">{t('register.alreadyAccount')} </span>
                <Link to="/login" className="text-crop-400 text-sm font-medium">{t('register.signIn')}</Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}