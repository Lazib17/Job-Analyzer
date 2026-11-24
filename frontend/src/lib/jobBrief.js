const LABELS = {
  en: {
    summary: 'In short',
    japanese: 'Japanese',
    skills: 'Skills they ask for',
    other: 'Other requirements',
    window: 'Application window',
    starts: 'Opens',
    deadline: 'Deadline',
    full: 'Full description',
    visa: 'Visa support',
    remote: 'Remote',
    hybrid: 'Hybrid',
    onsite: 'On-site',
    notStated: 'Not stated',
  },
  ja: {
    summary: '要約',
    japanese: '日本語',
    skills: '求められるスキル',
    other: 'その他の条件',
    window: '応募期間',
    starts: '開始',
    deadline: '締切',
    full: '全文',
    visa: 'ビザサポート',
    remote: 'リモート',
    hybrid: 'ハイブリッド',
    onsite: '出社',
    notStated: '記載なし',
  },
};

const JAPANESE_RULES = [
  [/日本語不問|japanese not required|no japanese/i, { en: 'Not required', ja: '不問' }],
  [/ネイティブ|native|fluent|\bN1\b/i, { en: 'Native / N1', ja: 'ネイティブ / N1' }],
  [/ビジネス|business/i, { en: 'Business', ja: 'ビジネス' }],
  [/中級|intermediate|\bN2\b/i, { en: 'Intermediate / N2', ja: '中級 / N2' }],
  [/日常会話|conversational|daily|\bN3\b|\bN4\b|\bN5\b|basic/i, { en: 'Daily conversation', ja: '日常会話' }],
];

const SKILL_PATTERN =
  /\b(Python|Java|JavaScript|TypeScript|React|Node\.js|SQL|Excel|AWS|Azure|GCP|Docker|Kubernetes|Figma|Photoshop|Illustrator|Salesforce|SAP|Tableau|Power BI|HTML|CSS|Go|Ruby|PHP|C\+\+|C#|Swift|Kotlin|Django|FastAPI|Vue|Angular|Git|Linux|English|TOEIC|JLPT)\b/gi;

const NOISE =
  /^(home|login|log in|register|sign up|employers|privacy|copyright|cookie|menu|search|faq|contact|日本語|english|career forum|my cfn)$/i;

function asText(value) {
  if (Array.isArray(value)) return value.filter(Boolean).join('\n');
  return value ? String(value) : '';
}

function linesOf(text) {
  return text
    .replace(/\r/g, '')
    .split('\n')
    .map((line) => line.replace(/\s+/g, ' ').trim())
    .filter((line) => line.length > 1 && !NOISE.test(line));
}

function unique(items, limit) {
  const seen = new Set();
  const kept = [];
  items.forEach((item) => {
    const clean = item.replace(/\s+/g, ' ').trim();
    const key = clean.toLowerCase();
    if (!clean || seen.has(key)) return;
    seen.add(key);
    kept.push(clean);
  });
  return kept.slice(0, limit);
}

function japaneseLevel(text, stored, lang) {
  const source = `${stored || ''}\n${text}`;
  for (const [pattern, label] of JAPANESE_RULES) {
    if (pattern.test(source)) return label[lang];
  }
  return stored ? stored : '';
}

function skillsFrom(text, requirements) {
  const tagged = requirements
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && line.length <= 40 && !/https?:/i.test(line));
  const found = text.match(SKILL_PATTERN) || [];
  return unique([...tagged, ...found], 8);
}

function otherRequirements(text) {
  const interesting = linesOf(text).filter((line) =>
    /必須|歓迎|応募資格|資格|学歴|未経験|経験|ビザ|visa|bachelor|degree|正社員|契約|full[- ]time|part[- ]time|週\d|年休|残業/i.test(line)
  );
  return unique(
    interesting.map((line) => (line.length > 140 ? `${line.slice(0, 137)}…` : line)),
    4
  );
}

function findDate(text, kind) {
  const rules =
    kind === 'deadline'
      ? /(?:締切|まで|deadline|apply by|closes|close date|due)[^\d]{0,24}(\d{4}[./年-]\s*\d{1,2}[./月-]\s*\d{1,2}日?)/i
      : /(?:開始|から|start|opens|open date|posted|掲載開始)[^\d]{0,24}(\d{4}[./年-]\s*\d{1,2}[./月-]\s*\d{1,2}日?)/i;
  const match = text.match(rules);
  return match ? match[1].replace(/\s+/g, '') : '';
}

function summaryFrom(text) {
  const body = linesOf(text)
    .filter((line) => line.length >= 40 && !/https?:/i.test(line))
    .slice(0, 6)
    .join(' ');
  if (!body) return '';
  const sentences = body.split(/(?<=[。．.!?])\s+/).filter((part) => part.length >= 30);
  const picked = (sentences.length ? sentences : [body]).slice(0, 2).join(' ');
  return picked.length > 320 ? `${picked.slice(0, 317)}…` : picked;
}

function workStyle(job, text, labels) {
  const blob = `${job.location || ''} ${text}`.toLowerCase();
  if (job.remote_option || /フルリモート|fully remote|\bremote\b|在宅/.test(blob)) {
    if (/ハイブリッド|hybrid/.test(blob)) return labels.hybrid;
    return labels.remote;
  }
  if (/ハイブリッド|hybrid/.test(blob)) return labels.hybrid;
  if (/出社|on-?site|office/.test(blob)) return labels.onsite;
  return '';
}

export function buildJobBrief(job, language) {
  const lang = language === 'ja' ? 'ja' : 'en';
  const labels = LABELS[lang];
  const description = asText(job?.description);
  const requirements = asText(job?.requirements);
  const text = `${description}\n${requirements}`;
  const japanese = japaneseLevel(text, job?.japanese_level, lang);
  const style = workStyle(job, text, labels);
  const visa = Boolean(job?.visa_sponsorship) || /visa support|ビザサポート|就労ビザ|sponsorship/i.test(text);

  return {
    labels,
    summary: summaryFrom(description),
    japanese,
    skills: skillsFrom(text, requirements),
    other: otherRequirements(text),
    starts: findDate(text, 'start'),
    deadline: findDate(text, 'deadline'),
    chips: [japanese && `${labels.japanese}: ${japanese}`, style, visa && labels.visa].filter(Boolean),
    fullText: description,
  };
}
