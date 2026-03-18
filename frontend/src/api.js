import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: API_URL })

export const getMessages = () => api.get('/api/messages').then(r => r.data)
export const getMessage = (id) => api.get(`/api/messages/${id}`).then(r => r.data)
export const createMessage = (msg) => api.post('/api/messages', msg).then(r => r.data)
export const updateMessage = (id, msg) => api.put(`/api/messages/${id}`, msg).then(r => r.data)
export const deleteMessage = (id) => api.delete(`/api/messages/${id}`).then(r => r.data)
export const deleteAllMessages = () => api.delete('/api/messages/all').then(r => r.data)

export const getBriefing = () => api.get('/api/briefing').then(r => r.data)

export const getRules = () => api.get('/api/rules').then(r => r.data)
export const createRule = (rule) => api.post('/api/rules', rule).then(r => r.data)
export const updateRule = (id, rule) => api.put(`/api/rules/${id}`, rule).then(r => r.data)
export const deleteRule = (id) => api.delete(`/api/rules/${id}`).then(r => r.data)

export default api
