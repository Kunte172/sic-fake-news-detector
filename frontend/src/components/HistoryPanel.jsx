import Feedback from './Feedback'
import { Icon } from './Theme'

export default function HistoryPanel({ history, pageLimit, token, onPage, onSaved, onExpired }) {
  const { items, total, offset, busy, error } = history
  return <section className="card history-panel" aria-labelledby="history-title">
    <div className="history-header">
      <div className="card-title"><span className="tile"><Icon name="file" /></span>
        <div><h2 id="history-title">Lịch sử phân tích</h2><p className="muted">{total} lượt đã lưu</p></div>
      </div>
      <button className="secondary small" type="button" disabled={busy} onClick={() => onPage(offset)}>
        {busy ? 'Đang tải…' : 'Làm mới'}
      </button>
    </div>
    {error && <p role="alert" className="notice error">{error}</p>}
    {!items.length && !error && <p className="muted history-empty" role="status">{busy ? 'Đang tải lịch sử…' : 'Các kết quả đã phân tích sẽ xuất hiện tại đây.'}</p>}
    {items.length > 0 && <div className="history-table-wrap">
      <table className="history-table">
        <caption className="sr-only">Danh sách các lượt phân tích đã lưu</caption>
        <thead><tr>
          <th>Thời gian</th>
          <th>Dữ liệu đã kiểm tra</th>
          <th>Kết quả</th>
          <th>Mức nghi ngờ</th>
          <th>Phản hồi</th>
        </tr></thead>
        <tbody>{items.map((item) => {
          const date = new Date(item.created_at)
          const isLikelyReal = item.label === 'LESS_SUSPICIOUS'
          const verdict = isLikelyReal ? 'Có dấu hiệu là tin thật' : 'Có dấu hiệu là tin giả'
          return <tr key={item.id}>
            <td className="history-date"><strong>{date.toLocaleDateString('vi-VN')}</strong><span>{date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}</span></td>
            <td className="history-content"><span className="history-type">{item.input_type === 'url' ? 'Đường dẫn URL' : 'Văn bản'}</span><p>{item.content_preview}</p></td>
            <td><span className={'history-verdict ' + (item.label === 'LESS_SUSPICIOUS' ? 'real' : 'fake')}>{verdict}</span></td>
            <td className="history-score">{Math.round((item.label === 'LESS_SUSPICIOUS' ? 1 - item.score : item.score) * 10000) / 100}%</td>
            <td><Feedback scope="history" item={item} token={token} onSaved={onSaved} onExpired={onExpired} /></td>
          </tr>
        })}</tbody>
      </table>
    </div>}
    {total > pageLimit && <div className="history-header pagination">
      <span className="muted">{offset + 1}–{Math.min(offset + items.length, total)} / {total}</span>
      <div className="actions">
        <button className="secondary small" disabled={busy || !offset} onClick={() => onPage(Math.max(0, offset - pageLimit))}>Trang trước</button>
        <button className="secondary small" disabled={busy || offset + pageLimit >= total} onClick={() => onPage(offset + pageLimit)}>Trang sau</button>
      </div>
    </div>}
  </section>
}
