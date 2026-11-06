import assert from 'node:assert/strict'
import { createServer } from 'vite'
import React from 'react'
import { renderToString } from 'react-dom/server'
const values = new Map()
globalThis.localStorage = { getItem: (key) => values.get(key) ?? null }
globalThis.matchMedia = () => ({ matches: false })
const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' })
try {
  const { default: App } = await server.ssrLoadModule('/src/App.jsx')
  assert.match(renderToString(React.createElement(App)), /Đăng nhập|Sign in/)
  values.set('sic_guest_mode', '1')
  const guest = renderToString(React.createElement(App))
  assert.match(guest, /input-mode/)
  assert.match(guest, /Phân tích/)
  const { default: Result } = await server.ssrLoadModule('/src/components/ResultCard.jsx')
  const html = renderToString(React.createElement(Result, { result: {
    label:'LESS_SUSPICIOUS', score:0.55, model_version:'fixture-svm', explanation: {
      disclaimer:'Not evidence of truth', terms:[{term:'read more', value:0.25, direction:'toward_fake'}],
      fake_margin:0.2, intercept:0.1, other_contribution:-0.15,
      lime:{fidelity:0.1,terms:[]},
    },
  }}))
  for (const text of ['read more', '0.2500', 'Not evidence of truth', 'độ tin cậy thấp']) assert.ok(html.includes(text), text)
  assert.match(html, /55/)
  assert.doesNotMatch(html, /Có dấu hiệu là tin thật/)
  console.log('PASS: auth/guest app render, explanation, LIME warning, non-inverted Fake score')
} finally { await server.close() }
