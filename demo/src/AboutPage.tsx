import { useEffect } from 'react'
import { COPIES, type Lang } from './copy'
import { DATASETS, type Results } from './data'
import LangLink from './components/LangLink'

// The about page: where the page's data comes from, how it was tested, and its limits, said once.
type Bit = string | { text: string; href: string }
type Section = { h: string; p: Bit[][] }

const TT = 'https://ads.tiktok.com/help/article/tiktok-ads-policy-'

const SECTIONS: Record<Lang, (r: Results) => Section[]> = {
  zh: (r) => [
    {
      h: '这是什么',
      p: [['一个审核广告的助手。它读出图片里的字，在政策库里查条款，判断广告有没有违规，并把广告原话和条款原文交给核对脚本逐字核对。广告主问哪里违规、怎么改时，它给出修改后的版本，再审核广告主交来的新版本。']],
    },
    {
      h: '政策从哪来',
      p: [
        ['中文广告按《中华人民共和国广告法》（2021 年修正），原文取自', { text: '北京市市场监督管理局网站', href: 'https://scjgj.beijing.gov.cn/cxfw/flfgcxfw/ggl/202204/t20220401_2646388.html' }, '，并和', { text: '上海市市场监督管理局网站', href: 'https://scjgj.sh.gov.cn/903/20250924/7e43b9954ca24b349488e5b464e83ac8.html' }, '的版本逐条比对过；另按市场监管总局的', { text: '《广告绝对化用语执法指南》', href: 'https://www.samr.gov.cn/ggjgs/tzgg/art/2023/art_183b5cb48d9e4f0dba67f9f912a913ba.html' }, '判断哪些“最”“第一”不算违规。'],
        ['英文广告按', { text: '平台公开的广告政策', href: `${TT}misleading-and-false-content` }, '的全球通用部分。政策库一共 32 条条款，是这些文件的摘录。'],
      ],
    },
    {
      h: '怎么测试的',
      p: [
        [`${r.ads} 条广告，中文、英文各 ${r.zh} 条，其中 ${r.images} 条是图片广告。每条违规的类别、对应的条款和广告里的原话，在写题时就定好；另有 30 条看着像违规、其实合规的广告。广告和品牌都是虚构的，图片由程序绘制。`],
        ['测试计划和文件指纹在运行前写好、冻结。审核助手和单个提示词各跑两遍，再和违禁词表、CLIP、SigLIP 2 以及三个开源审核模型比较：看图片的 SafeGuard-VL-RL，看文字的 Qwen3Guard 和 Granite Guardian。这三个是计划冻结后加的，各跑了一遍。'],
      ],
    },
    {
      h: '局限',
      p: [['测试用的广告比真实广告短、干净；喝酒的场景是插画，不是照片。只用了一个模型、每条跑两遍，相差一两条的差别在误差范围内。']],
    },
    {
      h: '用到的模型和工具',
      p: [
        ['审核：claude-haiku-5-5（effort medium）。读图：RapidOCR。核对引文：', { text: 'evidence-check', href: 'https://github.com/Jason-d-e/evidence-check' }, ' 的核对脚本。'],
        ['页面展示的是测试时存下的结果，页面本身不调用模型。'],
      ],
    },
  ],
  en: (r) => [
    {
      h: 'What it is',
      p: [['An assistant that reviews ads. It reads the words in an image, looks up clauses in a policy library, decides whether the ad breaks a rule, and sends the ad’s words and the clause’s words to a checker that finds each quote word for word. When the advertiser asks what is wrong and how to fix it, it writes a corrected version, then reviews the version the advertiser submits.']],
    },
    {
      h: 'Where the policies come from',
      p: [
        ['English ads are reviewed against the global sections of five pages of a platform’s published ad policies: ', { text: 'misleading and false content', href: `${TT}misleading-and-false-content?lang=en` }, ', ', { text: 'weight management', href: `${TT}weight-management?lang=en` }, ', ', { text: 'alcohol', href: `${TT}alcohol?lang=en` }, ', ', { text: 'deceptive practices', href: `${TT}deceptive-practices?lang=en` }, ' and ', { text: 'financial services', href: `${TT}financial-services?lang=en` }, '. The quotes are checked against those pages; this site names the section and links to it rather than copying the text.'],
        ['Chinese ads are reviewed against the Advertising Law of the PRC (2021 amendment), taken from the ', { text: 'Beijing market regulator’s website', href: 'https://scjgj.beijing.gov.cn/cxfw/flfgcxfw/ggl/202204/t20220401_2646388.html' }, ' and checked article by article against the ', { text: 'Shanghai regulator’s copy', href: 'https://scjgj.sh.gov.cn/903/20250924/7e43b9954ca24b349488e5b464e83ac8.html' }, ', and against the national market regulator’s ', { text: 'guide on absolute terms', href: 'https://www.samr.gov.cn/ggjgs/tzgg/art/2023/art_183b5cb48d9e4f0dba67f9f912a913ba.html' }, '. The library holds 32 clauses excerpted from these documents.'],
      ],
    },
    {
      h: 'How it was tested',
      p: [
        [`${r.ads} ads, ${r.zh} in Chinese and ${r.en} in English, ${r.images} of them image ads. For every violation, the category, the clause and the ad’s words were fixed when the ad was written; 30 more ads look risky but are allowed. The ads and brands are fictional, and the images are drawn by a script.`],
        ['The test plan and file fingerprints were written and frozen before the run. The review agent and one prompt ran twice each and were compared with a banned-word list, CLIP, SigLIP 2 and three open moderation models: SafeGuard-VL-RL for images, Qwen3Guard and Granite Guardian for text. The three moderation models were added after the plan was frozen and ran once.'],
      ],
    },
    {
      h: 'Limits',
      p: [['The test ads are shorter and cleaner than real ones, and the drinking scenes are illustrations, not photos. One model was used and each ad ran twice, so a difference of one or two ads is within noise.']],
    },
    {
      h: 'Models and tools',
      p: [
        ['Review: claude-haiku-5-5 at medium effort. Reading images: RapidOCR. Checking quotes: the checker script of ', { text: 'evidence-check', href: 'https://github.com/Jason-d-e/evidence-check' }, '.'],
        ['The page shows results stored during testing and does not call a model.'],
      ],
    },
  ],
}

export default function AboutPage({ lang }: { lang: Lang }) {
  const t = COPIES[lang]
  const sections = SECTIONS[lang](DATASETS[lang].results)
  useEffect(() => {
    document.documentElement.lang = t.htmlLang
  }, [t])
  return (
    <div className="pg">
      <a className="skip" href="#main">{t.skip}</a>
      <header className="bar">
        <div className="container bar-inner">
          <a className="logo" href={t.home}>
            <svg width="22" height="22" viewBox="0 0 32 32" aria-hidden><rect x="5" y="6" width="22" height="20" rx="5" fill="none" stroke="currentColor" strokeWidth="3" /><path d="M11 16.5l3.6 3.5L21.5 12" fill="none" stroke="var(--color-accent)" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
            <span className="logo-name">{t.brand}</span>
          </a>
          <LangLink t={t} href={t.other.about} />
        </div>
      </header>
      <main id="main" className="about">
        <div className="container">
          <div className="about-inner">
            <h1>{t.about.title}</h1>
            {sections.map((s) => (
              <section key={s.h} className="about-sec">
                <h2>{s.h}</h2>
                {s.p.map((para, i) => (
                  <p key={i}>{para.map((bit, j) => (typeof bit === 'string' ? bit : <a key={j} href={bit.href}>{bit.text}</a>))}</p>
                ))}
              </section>
            ))}
            <a className="btn btn--clear" href={t.home}>{t.about.back}</a>
          </div>
        </div>
      </main>
    </div>
  )
}
