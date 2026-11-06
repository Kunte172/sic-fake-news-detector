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
 values.set('sic_guest_mode','1')
 assert.match(renderToString(React.createElement(App)), /input-mode/)
 values.clear(); values.set('sic_access_token','test-expired-token')
 assert.match(renderToString(React.createElement(App)), /Đang kiểm tra phiên/)
 console.log('PASS: auth, guest and pending-session render without ReferenceError')
} finally { await server.close() }
