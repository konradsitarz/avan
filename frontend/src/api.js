import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: API_URL })

export const getMessages = () => api.get('/api/messages').then(r => r.data)
export const getMessage = (id) => api.get(`/api/messages/${id}`).then(r => r.data)
export const createMessage = (msg) => api.post('/api/messages', msg).then(r => r.data)
export const updateMessage = (id, msg) => api.put(`/api/messages/${id}`, msg).then(r => r.data)
export const deleteMessage = (id) => api.delete(`/api/messages/${id}`).then(r => r.data)
export const deleteAllMessages = () => api.delete('/api/messages/all').then(r => r.data)
export const overrideMessage = (id, override) => api.post(`/api/messages/${id}/override`, override).then(r => r.data)
export const generateReply = (id, tone) => api.post(`/api/messages/${id}/generate-reply`, { tone }).then(r => r.data)

export const getBriefing = () => api.get('/api/briefing').then(r => r.data)
export const textToSpeech = (text, voiceId) =>
  api.post('/api/tts', { text, voice_id: voiceId }, { responseType: 'blob' }).then(r => r.data)

export default api
