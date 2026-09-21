import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from '../i18n/useTranslation'
import { LANGS, LANG_LABELS, type Lang, type TranslationKey } from '../i18n/translations'

const PROOF: { src: string; altKey: TranslationKey }[] = [
  { src: '/landing/thumbnail-hormuz.jpg', altKey: 'landing.proof.hormuz' },
  { src: '/landing/thumbnail-f15e.jpg', altKey: 'landing.proof.f15e' },
  { src: '/landing/thumbnail-nk.jpg', altKey: 'landing.proof.nk' },
  { src: '/landing/thumbnail-resolve.jpg', altKey: 'landing.proof.resolve' },
]

const STEPS: { titleKey: TranslationKey; bodyKey: TranslationKey }[] = [
  { titleKey: 'landing.step1.title', bodyKey: 'landing.step1.body' },
  { titleKey: 'landing.step2.title', bodyKey: 'landing.step2.body' },
  { titleKey: 'landing.step3.title', bodyKey: 'landing.step3.body' },
]

const STAGES: { titleKey: TranslationKey; bodyKey: TranslationKey }[] = [
  { titleKey: 'landing.stage.refs', bodyKey: 'landing.stage.refsBody' },
  { titleKey: 'landing.stage.image', bodyKey: 'landing.stage.imageBody' },
  { titleKey: 'landing.stage.video', bodyKey: 'landing.stage.videoBody' },
  { titleKey: 'landing.stage.concat', bodyKey: 'landing.stage.concatBody' },
]

const FAQS: { qKey: TranslationKey; aKey: TranslationKey }[] = [
  { qKey: 'landing.faq1.q', aKey: 'landing.faq1.a' },
  { qKey: 'landing.faq2.q', aKey: 'landing.faq2.a' },
  { qKey: 'landing.faq3.q', aKey: 'landing.faq3.a' },
  { qKey: 'landing.faq4.q', aKey: 'landing.faq4.a' },
]

function LangSelect() {
  const { lang, setLang } = useTranslation()
  return (
    <select
      value={lang}
      onChange={e => setLang(e.target.value as Lang)}
      aria-label="Language"
      className="text-xs px-2 py-2 rounded-lg outline-none cursor-pointer"
      style={{ background: 'var(--card)', color: 'var(--text)', border: '1px solid var(--border)', minHeight: 44 }}
    >
      {LANGS.map(l => (
        <option key={l} value={l}>{LANG_LABELS[l]}</option>
      ))}
    </select>
  )
}

function PrimaryLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center justify-center rounded-lg px-5 text-sm font-semibold cursor-pointer"
      style={{ background: 'var(--accent)', color: '#fff', minHeight: 44 }}
    >
      {children}
    </Link>
  )
}

function GhostLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center justify-center rounded-lg px-5 text-sm font-semibold cursor-pointer"
      style={{ border: '1px solid var(--border)', color: 'var(--text)', minHeight: 44 }}
    >
      {children}
    </Link>
  )
}

export default function LandingPage() {
  const { t } = useTranslation()

  return (
    <div className="min-h-dvh flex flex-col" style={{ background: 'var(--bg)', color: 'var(--text)', fontFamily: "'Geist Variable', sans-serif" }}>
      <header className="flex flex-wrap items-center gap-3 px-5 py-4 border-b" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
        <span className="w-[22px] h-[22px] rounded flex items-center justify-center text-xs font-bold" style={{ background: 'var(--accent)', color: 'var(--bg)' }}>F</span>
        <span className="text-xs font-bold tracking-widest">{t('app.brandName')}</span>
        <span className="ml-auto" />
        <LangSelect />
        <GhostLink to="/huongdan">{t('landing.nav.guide')}</GhostLink>
        <PrimaryLink to="/dashboard">{t('landing.nav.console')}</PrimaryLink>
      </header>

      <main className="flex-1 mx-auto w-full max-w-5xl px-5 py-12 flex flex-col gap-16">
        <section className="flex flex-col gap-5 max-w-2xl">
          <p className="text-xs tracking-wide uppercase m-0" style={{ color: 'var(--accent)' }}>{t('landing.pre')}</p>
          <h1 className="text-3xl sm:text-4xl font-semibold leading-tight m-0">{t('landing.headline')}</h1>
          <p className="text-base leading-relaxed m-0" style={{ color: 'var(--muted)' }}>{t('landing.sub')}</p>
          <div className="flex flex-wrap gap-3">
            <PrimaryLink to="/dashboard">{t('landing.cta.primary')}</PrimaryLink>
            <GhostLink to="/huongdan">{t('landing.cta.secondary')}</GhostLink>
          </div>
          <p className="text-xs m-0" style={{ color: 'var(--muted)' }}>{t('landing.micro')}</p>
        </section>

        <section className="flex flex-col gap-4">
          <h2 className="text-sm font-semibold tracking-wide uppercase m-0" style={{ color: 'var(--muted)' }}>{t('landing.proof.title')}</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {PROOF.map(item => (
              <figure key={item.src} className="m-0 overflow-hidden rounded-xl" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
                <img src={item.src} alt={t(item.altKey)} width={480} height={270} className="w-full h-auto block" />
              </figure>
            ))}
          </div>
        </section>

        <section className="flex flex-col gap-5">
          <h2 className="text-sm font-semibold tracking-wide uppercase m-0" style={{ color: 'var(--muted)' }}>{t('landing.steps.title')}</h2>
          <ol className="grid gap-4 md:grid-cols-3 list-none p-0 m-0">
            {STEPS.map((s, i) => (
              <li key={s.titleKey} className="rounded-xl p-4 flex flex-col gap-2" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
                <span className="text-xs font-bold" style={{ color: 'var(--accent)' }}>{i + 1}</span>
                <h3 className="text-sm font-semibold m-0">{t(s.titleKey)}</h3>
                <p className="text-sm leading-relaxed m-0" style={{ color: 'var(--muted)' }}>{t(s.bodyKey)}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="flex flex-col gap-5">
          <h2 className="text-sm font-semibold tracking-wide uppercase m-0" style={{ color: 'var(--muted)' }}>{t('landing.stages.title')}</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {STAGES.map(s => (
              <div key={s.titleKey} className="rounded-xl p-4 flex flex-col gap-1" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
                <h3 className="text-sm font-semibold m-0">{t(s.titleKey)}</h3>
                <p className="text-sm m-0" style={{ color: 'var(--muted)' }}>{t(s.bodyKey)}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="flex flex-col gap-4 max-w-2xl">
          <h2 className="text-sm font-semibold tracking-wide uppercase m-0" style={{ color: 'var(--muted)' }}>{t('landing.faq.title')}</h2>
          {FAQS.map(f => (
            <div key={f.qKey} className="flex flex-col gap-1 pb-4" style={{ borderBottom: '1px solid var(--border)' }}>
              <h3 className="text-sm font-semibold m-0">{t(f.qKey)}</h3>
              <p className="text-sm leading-relaxed m-0" style={{ color: 'var(--muted)' }}>{t(f.aKey)}</p>
            </div>
          ))}
        </section>

        <section className="rounded-xl p-6 flex flex-col gap-4 items-start" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
          <h2 className="text-lg font-semibold m-0">{t('landing.final.title')}</h2>
          <PrimaryLink to="/dashboard">{t('landing.final.cta')}</PrimaryLink>
        </section>
      </main>

      <footer className="px-5 py-4 text-xs" style={{ color: 'var(--muted)', borderTop: '1px solid var(--border)' }}>
        {t('landing.footer')}
      </footer>
    </div>
  )
}
