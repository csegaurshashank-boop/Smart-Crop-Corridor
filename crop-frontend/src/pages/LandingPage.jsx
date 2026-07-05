import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Leaf, ArrowRight, Satellite, Cpu, Shield } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '../components/LanguageSwitcher'

export default function LandingPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-earth-950 relative overflow-hidden">
      <div className="absolute inset-0 bg-field-pattern opacity-30" />
      <div className="hidden sm:block absolute top-20 left-10 w-96 h-96 bg-crop-900/20 rounded-full blur-3xl" />
      <div className="hidden sm:block absolute bottom-20 right-10 w-80 h-80 bg-soil-900/20 rounded-full blur-3xl" />

      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {/* Nav */}
        <nav className="flex items-center justify-between gap-3 mb-10 sm:mb-20">
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="w-8 h-8 bg-crop-600 rounded-lg flex items-center justify-center">
              <Leaf size={16} className="text-white" />
            </div>
            <span className="font-display font-semibold text-earth-100 text-lg">CropCorridor</span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
            <LanguageSwitcher />
            <button onClick={() => navigate('/login')} className="btn-secondary text-xs sm:text-sm py-2 px-3 sm:px-5">
              {t('nav.signIn')}
            </button>
            <button onClick={() => navigate('/register')} className="btn-primary text-xs sm:text-sm py-2 px-3 sm:px-5 hidden sm:inline-flex">
              {t('nav.getStarted')}
            </button>
          </div>
        </nav>

        {/* Hero */}
        <div className="text-center mb-24">
          <div className="inline-flex items-center gap-2 bg-crop-900/30 border border-crop-800/40 rounded-full px-4 py-2 mb-8">
            <Satellite size={14} className="text-crop-400" />
            <span className="text-crop-400 text-xs font-body font-medium tracking-wider uppercase">
              {t('landing.badge')}
            </span>
          </div>
          <h1 className="font-display text-4xl sm:text-6xl md:text-7xl font-bold text-earth-50 leading-tight mb-6">
            {t('landing.title1')}<br />
            <span className="text-crop-400">{t('landing.title2')}</span><br />
            {t('landing.title3')}
          </h1>
          <p className="text-earth-400 text-lg font-body max-w-xl mx-auto mb-10 leading-relaxed">
            {t('landing.subtitle')}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button onClick={() => navigate('/register')}
              className="btn-primary flex items-center gap-2 text-base py-4 px-8">
              {t('landing.startBtn')} <ArrowRight size={18} />
            </button>
            <button onClick={() => navigate('/login')}
              className="text-earth-400 hover:text-earth-200 font-body text-sm transition-colors underline underline-offset-4">
              {t('landing.alreadyAccount')}
            </button>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20">
          {[
            { icon: <Satellite size={20} className="text-crop-400" />, title: t('landing.feature1Title'), desc: t('landing.feature1Desc') },
            { icon: <Cpu size={20} className="text-soil-400" />, title: t('landing.feature2Title'), desc: t('landing.feature2Desc') },
            { icon: <Shield size={20} className="text-blue-400" />, title: t('landing.feature3Title'), desc: t('landing.feature3Desc') },
          ].map((f, i) => (
            <div key={i} className="glass-card rounded-2xl p-6 hover:border-earth-600 transition-all duration-300">
              <div className="w-10 h-10 bg-earth-800 rounded-xl flex items-center justify-center mb-4">{f.icon}</div>
              <h3 className="font-display text-earth-100 text-lg font-semibold mb-2">{f.title}</h3>
              <p className="text-earth-500 text-sm font-body leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

        {/* Stats */}
        <div className="glass-card rounded-2xl p-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {[
              { value: '5×5', label: t('landing.stat1') },
              { value: 'NDVI', label: t('landing.stat2') },
              { value: 'Real-time', label: t('landing.stat3') },
              { value: 'AI', label: t('landing.stat4') },
            ].map((s, i) => (
              <div key={i}>
                <div className="font-display text-2xl font-bold text-crop-400 mb-1">{s.value}</div>
                <div className="text-earth-500 text-xs font-body uppercase tracking-wider">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}