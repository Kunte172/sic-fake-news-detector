const base = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '')

export async function api(path, { token, body, signal } = {}) {
  const response = await fetch(base + '/api/v1' + path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: {
      ...(body !== undefined && { 'Content-Type': 'application/json' }),
      ...(token && { Authorization: 'Bearer ' + token }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const error = new Error(typeof data?.detail === 'string' ? data.detail : 'Yêu cầu chưa hoàn tất.')
    error.status = response.status
    throw error
  }
  if (!data) throw new Error('Máy chủ trả về dữ liệu không hợp lệ.')
  return data
}
