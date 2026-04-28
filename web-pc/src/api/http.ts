import axios from 'axios'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    return Promise.reject(error)
  },
)
