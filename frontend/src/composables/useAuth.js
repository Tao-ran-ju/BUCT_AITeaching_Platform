import { ref } from 'vue'

const TOKEN_KEY = 'buct_access_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  }
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

// 学生端 SSO 免登跳转时携带 ?token=<JWT>，读取后写入 localStorage 并抹掉地址栏参数。
export function readTokenFromUrl() {
  try {
    const params = new URLSearchParams(location.search)
    const token = params.get('token')
    if (token) {
      setToken(token)
      params.delete('token')
      const qs = params.toString()
      const clean = location.pathname + (qs ? '?' + qs : '') + location.hash
      history.replaceState(null, '', clean)
    }
  } catch (e) {
    /* ignore */
  }
}

// 轻量鉴权组合式：当前 token 是否已注入。
export function useAuth() {
  const token = ref(getToken())
  return { token }
}
