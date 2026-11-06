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
  const isLikelyReal = result?.label === 'LESS_SUSPICIOUS'
  const displayScore = score === null ? null : isLikelyReal ? Math.round((100 - score) * 100) / 100 : score
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
          <p className="score-number">{displayScore.toLocaleString('vi-VN', { maximumFractionDigits: 2 })}<span>%</span></p>
          <p className={'score-verdict ' + (isLikelyReal ? 'real' : 'fake')}>
            {isLikelyReal ? 'Có dấu hiệu là tin thật' : 'Có dấu hiệu là tin giả'}
          </p>
          <p className="muted">{isLikelyReal ? 'Mức độ tin thật theo mô hình' : 'Mức độ nghi ngờ tin giả'} — cần kiểm chứng thêm</p>
          <meter min="0" max="100" value={displayScore} aria-label={isLikelyReal ? 'Mức độ tin thật' : 'Mức độ nghi ngờ tin giả'}>{displayScore}%</meter>
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
        {result.explanation && <div className="explanation">
          <strong>Vì sao mô hình đưa ra kết quả này?</strong>
          <div className="explanation-terms">
            {(result.explanation.terms || []).slice(0, 6).map((term) => (
              <span key={term.term} className={term.direction === 'toward_fake' ? 'term-fake' : 'term-real'}>
                {term.term}
              </span>
            ))}
          </div>
          <p className="muted">{result.explanation.disclaimer}</p>
          {result.explanation.lime_unavailable && <p className="muted">LIME chưa được cài nên chỉ hiển thị đóng góp TF-IDF.</p>}
        </div>}
        {children}
      </div> : <div className="result-state">
        <div className="result-illustration"><Icon name="scan" size={38} /></div>
        <strong>Đang chờ bài báo</strong>
        <p className="muted">Dán nội dung và bấm Phân tích để xem kết quả.</p>
      </div>}
    </div>
  </section>
}
