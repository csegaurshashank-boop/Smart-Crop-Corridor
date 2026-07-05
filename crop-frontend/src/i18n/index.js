import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import en from './locales/en.json'
import hi from './locales/hi.json'

i18n
  .use(LanguageDetector)       // auto detect browser language
  .use(initReactI18next)       // connect to React
  .init({
    resources: {
      en: { translation: en },
      hi: { translation: hi },
    },
    fallbackLng: 'en',         // default to English if detection fails
    interpolation: {
      escapeValue: false,      // React already escapes values
    },
    detection: {
      order: ['localStorage', 'navigator'],
      cacheUserLanguage: true, // saves chosen language in localStorage
    },
  })

export default i18n