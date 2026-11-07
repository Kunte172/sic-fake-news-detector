import { Icon } from './Theme'

export function Verdict({ label, reviewStatus, decision }) {
  const suspicious = label === 'SUSPICIOUS'
  const likely = label === 'LESS_SUSPICIOUS'
  const needsReview = decision === 'NEEDS_REVIEW' || reviewStatus !== 'CONFIRMED'
  return <span className={'verdict ' + (needsReview ? 'neutral' : suspicious ? 'risky' : likely ? 'likely' : 'neutral')}>
    <Icon size={15} name={needsReview || !likely ? 'warning' : 'check'} />
    {needsReview ? 'Cần kiểm chứng' : suspicious ? 'Đáng ngờ' : likely ? 'Ít dấu hiệu đáng ngờ' : 'Chưa xác định'}
  </span>
}

export default function ResultCard({ result, loading, error, children }) {
  const score = Number.isFinite(result?.score)
    ? Math.max(0, Math.min(100, Math.round(result.score * 10000) / 100))
    : null
  return <section className="card result-card" aria-labelledby="result-title">
    <div className="card-title"><span className="tile"><Icon name="scan" /></span>
      <div><h2 id="result-title">Kết quả phân tích</h2><p className="muted">Điểm dự đoán của mô hình</p></div>
    </div>
    <div aria-live="polite">
      {loading ? <div className="result-state" role="status">
        <div className="skeleton skeleton-round" aria-hidden="true" />
        <div className="skeleton skeleton-line" aria-hidden="true" />
        <p>Đang phân tích bài báo…</p>
      </div> : error ? <div className="notice error result-error" role="alert"><Icon name="warning" />
        <div><strong>Chưa thể phân tích</strong><p>{error}</p></div>
      </div> : result ? <div className="result-content">
        <Verdict label={result.label} reviewStatus={result.review_status} decision={result.decision} />
        {score !== null && <>
          <p className="score-number">{score.toLocaleString('vi-VN', { maximumFractionDigits: 2 })}<span>%</span></p>
          <p className="score-verdict">
            Điểm lớp Fake của mô hình
          </p>
          <p className="muted">Điểm lớp Fake của mô hình — cần kiểm chứng thêm</p>
          <meter min="0" max="100" value={score} aria-label="Điểm lớp Fake của mô hình">{score}%</meter>
        </>}
        <p className="model-meta">Mô hình {result.model_version}</p>
        <p className="notice warning">Cần kiểm chứng độc lập: điểm này không xác nhận bài báo là thật hay giả.</p>
        {result.source_scope === 'external_url' && <p className="notice warning">
          Bài lấy từ nguồn bên ngoài dữ liệu huấn luyện; mô hình có thể nhận diện sai văn phong của nguồn này.
        </p>}
        <p className="model-meta">Phạm vi: {result.source_scope === 'external_url' ? result.source_domain : 'văn bản dán trực tiếp'}</p>
        {result.verification && <div className="verification">
          <strong>Kiểm chứng thông tin</strong>
          <p className="verification-conclusion">{result.verification.conclusion}</p>
          {result.verification.sources?.length
            ? <small>{result.verification.sources.length} nguồn kiểm chứng được tìm thấy.</small>
            : <small>Chưa tìm thấy nguồn kiểm chứng phù hợp.</small>}
        </div>}
        {result.explanation ? <div className="explanation">
          <h3>Lý do mô hình dự đoán</h3>
          <p className="muted">{result.explanation.disclaimer || 'Đây là hành vi mô hình, không phải bằng chứng sự thật.'}</p>
          <p>Dương nghiêng về Fake; âm nghiêng về Real. Đóng góp vào margin, không phải phần trăm.</p>
          <ul className="contribution-list">{(result.explanation.terms || []).map((term) => (
            <li key={term.term} className={term.direction === 'toward_fake' ? 'term-fake' : 'term-real'}>
              <strong>{term.term}</strong><span>{Number.isFinite(term.value) ? term.value.toFixed(4) : '—'}</span>
            </li>
          ))}</ul>
          <p className="model-meta">Margin Fake: {result.explanation.fake_margin?.toFixed(4) ?? '—'} · Hệ số chặn: {result.explanation.intercept?.toFixed(4) ?? '—'} · Phần còn lại: {result.explanation.other_contribution?.toFixed(4) ?? '—'}</p>
          {result.explanation.lime && <details>
            <summary>LIME — giải thích xấp xỉ cục bộ</summary>
            <p>Fidelity (R²): {result.explanation.lime.fidelity ?? 'chưa xác định'}</p>
            {(result.explanation.lime.fidelity == null || result.explanation.lime.fidelity < 0.5) && <p className="notice warning">Giải thích có độ tin cậy thấp. Không dựa vào các từ này để kết luận bài thật/giả.</p>}
            <ul>{(result.explanation.lime.terms || []).map((term) => <li key={term.term}>{term.term}: {term.weight?.toFixed(4)}</li>)}</ul>
          </details>}
          {result.explanation.lime_unavailable && <p className="muted">LIME chưa sẵn sàng; đang hiển thị đóng góp TF-IDF.</p>}
        </div> : <p className="muted">Mô hình đang dùng chưa cung cấp giải thích. Cần cấu hình artifact ML-01, report và calibration.</p>}
        {children}
      </div> : <div className="result-state">
        <div className="result-illustration"><Icon name="scan" size={38} /></div>
        <strong>Đang chờ bài báo</strong>
        <p className="muted">Dán nội dung và bấm Phân tích để xem kết quả.</p>
      </div>}
    </div>
  </section>
}
