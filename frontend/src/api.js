import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.response.use(
  r => r,
  err => {
    const msg = err.response?.data?.detail?.erro || err.response?.data?.detail || err.message
    return Promise.reject(new Error(msg))
  }
)

export default api
