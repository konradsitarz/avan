export const priorityLabels = {
  urgent: 'urgent',
  high: 'high',
  medium: 'medium',
  low: 'low',
}

export const categoryLabels = {
  safety: 'safety',
  plumbing: 'plumbing',
  electrical: 'electrical',
  noise: 'noise',
  maintenance: 'maintenance',
  billing: 'billing',
  access: 'access',
  compliance: 'compliance',
  other: 'other',
}

export const channelLabels = {
  email: 'email',
  sms: 'SMS',
  voice: 'phone',
}

export const label = (map, value) => map[value] || value
