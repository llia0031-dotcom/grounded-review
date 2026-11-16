import { useEffect, useState } from 'react'
import { COPIES, type Lang } from './copy'
import { DATASETS, DataContext } from './data'
import Bar from './components/Bar'
import Hero from './components/Hero'
import Tagline from './components/Tagline'
import Steps from './components/Steps'
import Demo from './components/Demo'
import Followup from './components/Followup'
import Results from './components/Results'
import Faq from './components/Faq'
import Close from './components/Close'
import Footer from './components/Footer'

export default function App({ lang }: { lang: Lang }) {
  const [still, setStill] = useState(false)
  const t = COPIES[lang]

  useEffect(() => {
    document.documentElement.lang = t.htmlLang
    document.title = t.title
  }, [t])

  return (
    <DataContext.Provider value={DATASETS[lang]}>
      <div className="pg" id="top">
        <a className="skip" href="#main">{t.skip}</a>
        <Bar t={t} />
        <main id="main">
          <Hero t={t} still={still} onToggleStill={() => setStill((s) => !s)} />
          <Tagline lines={t.tagline} lang={t.lang} />
          <Steps t={t} lang={t.lang} />
          <Demo t={t} />
          <Followup t={t} />
          <Results t={t} />
          <Faq t={t} />
          <Close t={t} />
        </main>
        <Footer t={t} />
      </div>
    </DataContext.Provider>
  )
}
