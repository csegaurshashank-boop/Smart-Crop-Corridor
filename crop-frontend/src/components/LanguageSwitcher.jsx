import React from 'react'
import { useTranslation } from 'react-i18next'

export default function LanguageSwitcher({ className = '' }) {
  const { i18n } = useTranslation()
  const current = i18n.language?.startsWith('hi') ? 'hi' : 'en'

  const toggle = (lang) => {
    i18n.changeLanguage(lang)
  }

  return (
    <div className={`flex items-center bg-earth-900 border border-earth-700 rounded-xl p-1 ${className}`}>
      <button
        onClick={() => toggle('en')}
        className={`px-3 py-1.5 rounded-lg text-xs font-body font-medium transition-all duration-200 ${
          current === 'en'
            ? 'bg-earth-700 text-earth-100 shadow-sm'
            : 'text-earth-500 hover:text-earth-300'
        }`}
      >
        EN
      </button>
      <button
        onClick={() => toggle('hi')}
        className={`px-3 py-1.5 rounded-lg text-xs font-body font-medium transition-all duration-200 ${
          current === 'hi'
            ? 'bg-earth-700 text-earth-100 shadow-sm'
            : 'text-earth-500 hover:text-earth-300'
        }`}
      >
        हिंदी
      </button>
    </div>
  )
}