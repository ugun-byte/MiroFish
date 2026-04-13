import { createI18n } from 'vue-i18n'
import languages from '../../../locales/languages.json'

const localeFiles = import.meta.glob('../../../locales/!(languages).json', { eager: true })

const messages = {}
const availableLocales = []

for (const path in localeFiles) {
  const key = path.match(/\/([^/]+)\.json$/)[1]
  if (languages[key]) {
    messages[key] = localeFiles[path].default
    availableLocales.push({ key, label: languages[key].label })
  }
}

let savedLocale = localStorage.getItem('locale') || 'ko'

// 기존에 'zh'(중국어)로 저장된 사용자가 있다면 강제로 'ko'(한국어)로 초기화
if (savedLocale === 'zh') {
  savedLocale = 'ko'
  localStorage.setItem('locale', 'ko')
}
const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'ko',
  messages
})

export { availableLocales }
export default i18n
