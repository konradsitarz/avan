export const priorityLabels = {
  urgent: 'pilny',
  high: 'wysoki',
  medium: 'średni',
  low: 'niski',
}

export const categoryLabels = {
  safety: 'bezpieczeństwo',
  plumbing: 'hydraulika',
  electrical: 'elektryka',
  noise: 'hałas',
  maintenance: 'konserwacja',
  billing: 'rozliczenia',
  access: 'dostęp',
  compliance: 'regulamin',
  other: 'inne',
}

export const channelLabels = {
  email: 'email',
  sms: 'SMS',
  voice: 'telefon',
}

export const label = (map, value) => map[value] || value
