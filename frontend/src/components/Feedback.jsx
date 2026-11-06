import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

export default function Feedback({ scope, item, token, onSaved, onExpired }) {
  const [comment, setComment] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const request = useRef(null)
  useEffect(() => () => request.current?.abort(), [])
  if (!item.id) return null
  if (item.feedback) return <div className="feedback">
    <p><strong>Phản hồi đã gửi.</strong> {item.feedback.agree ? 'Đồng ý' : 'Không đồng ý'} với kết quả.</p>
    {item.feedback.comment && <p className="muted">{item.feedback.comment}</p>}
  </div>

  async function submit(agree) {
    if (request.current) return
    const controller = new AbortController()
    request.current = controller
    setBusy(true)
    setError('')
    try {
      const text = comment.trim()
      const data = await api('/analyses/' + item.id + '/feedback', {
        token, body: { agree, ...(text && { comment: text }) }, signal: controller.signal,
      })
      if (!controller.signal.aborted) onSaved(item.id, data)
    } catch (cause) {
      if (controller.signal.aborted) return
      if (cause.status === 401) onExpired()
      else setError(cause.status === 409 ? 'Kết quả này đã có phản hồi. Hãy làm mới lịch sử.'
        : cause.status === 404 ? 'Không tìm thấy lượt phân tích của tài khoản này.'
        : cause.status === 422 ? 'Ghi chú chỉ được dài tối đa 1.000 ký tự.'
        : 'Chưa gửi được phản hồi. Vui lòng thử lại.')
    } finally {
      request.current = null
      if (!controller.signal.aborted) setBusy(false)
    }
  }

  const id = scope + '-comment-' + item.id
  return <div className="feedback">
    <label htmlFor={id}>Phản hồi về kết quả <span className="muted">(tùy chọn)</span></label>
    <input id={id} value={comment} maxLength={1000} onChange={(e) => setComment(e.target.value)}
      disabled={busy} placeholder="Thêm ghi chú…" />
    <div className="actions">
      <button type="button" className="secondary small" disabled={busy} onClick={() => submit(true)}>Đồng ý</button>
      <button type="button" className="secondary small" disabled={busy} onClick={() => submit(false)}>Không đồng ý</button>
    </div>
    {busy && <p className="muted" role="status">Đang gửi phản hồi…</p>}
    {error && <p className="notice error" role="alert">{error}</p>}
  </div>
}
