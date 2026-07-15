const TEAM_FLAG_CODE_BY_KEY: Record<string, string> = {
  algeria: 'dz',
  angola: 'ao',
  argentina: 'ar',
  australia: 'au',
  austria: 'at',
  belgium: 'be',
  bolivia: 'bo',
  bosniaandherzegovina: 'ba',
  brazil: 'br',
  bulgaria: 'bg',
  cameroon: 'cm',
  canada: 'ca',
  capeverde: 'cv',
  chile: 'cl',
  china: 'cn',
  colombia: 'co',
  costarica: 'cr',
  croatia: 'hr',
  cuba: 'cu',
  curacao: 'cw',
  czechrepublic: 'cz',
  czechoslovakia: 'cz',
  denmark: 'dk',
  drcongo: 'cd',
  dutcheastindies: 'id',
  eastgermany: 'de',
  ecuador: 'ec',
  egypt: 'eg',
  elsalvador: 'sv',
  england: 'gb-eng',
  france: 'fr',
  germany: 'de',
  ghana: 'gh',
  greece: 'gr',
  haiti: 'ht',
  honduras: 'hn',
  hungary: 'hu',
  iceland: 'is',
  iran: 'ir',
  iriran: 'ir',
  iraq: 'iq',
  ireland: 'ie',
  israel: 'il',
  italy: 'it',
  ivorycoast: 'ci',
  jamaica: 'jm',
  japan: 'jp',
  jordan: 'jo',
  koreadpr: 'kp',
  korearepublic: 'kr',
  kuwait: 'kw',
  mexico: 'mx',
  morocco: 'ma',
  netherlands: 'nl',
  newzealand: 'nz',
  nigeria: 'ng',
  northkorea: 'kp',
  northernireland: 'gb-nir',
  norway: 'no',
  panama: 'pa',
  paraguay: 'py',
  peru: 'pe',
  poland: 'pl',
  portugal: 'pt',
  qatar: 'qa',
  republicofireland: 'ie',
  romania: 'ro',
  russia: 'ru',
  saudiarabia: 'sa',
  scotland: 'gb-sct',
  senegal: 'sn',
  serbia: 'rs',
  serbiaandmontenegro: 'rs',
  slovakia: 'sk',
  slovenia: 'si',
  southafrica: 'za',
  southkorea: 'kr',
  sovietunion: 'ru',
  spain: 'es',
  sweden: 'se',
  switzerland: 'ch',
  togo: 'tg',
  trinidadandtobago: 'tt',
  tunisia: 'tn',
  turkey: 'tr',
  turkiye: 'tr',
  ukraine: 'ua',
  unitedarabemirates: 'ae',
  unitedstates: 'us',
  unitedstatesofamerica: 'us',
  usa: 'us',
  uruguay: 'uy',
  uzbekistan: 'uz',
  wales: 'gb-wls',
  westgermany: 'de',
  yugoslavia: 'rs',
  zaire: 'cd',
}

export interface TeamFlag {
  display: string
  imageUrl: string | null
  label: string
  isFallback: boolean
}

function normalizeTeamKey(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/&/g, 'and')
    .replace(/[^a-zA-Z0-9]/g, '')
    .toLowerCase()
}

function initials(teamName: string): string {
  return teamName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

export function getTeamFlag(teamName: string, teamId: string): TeamFlag {
  const flagCode =
    TEAM_FLAG_CODE_BY_KEY[normalizeTeamKey(teamName)] ?? TEAM_FLAG_CODE_BY_KEY[normalizeTeamKey(teamId)]

  if (flagCode) {
    return {
      display: initials(teamName || teamId) || '?',
      imageUrl: `https://flagcdn.com/${flagCode}.svg`,
      label: `${teamName} flag`,
      isFallback: false,
    }
  }

  return {
    display: initials(teamName || teamId) || '?',
    imageUrl: null,
    label: `${teamName} initials`,
    isFallback: true,
  }
}
