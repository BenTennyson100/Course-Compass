/**
 * Reads an SSE stream from a POST endpoint.
 * The backend sends: data: {"token":"..."}\n\n  and  data: {"done":true}\n\n
 *
 * @param {string}   url       - API endpoint
 * @param {object}   body      - JSON body
 * @param {function} onToken   - called with each text token
 * @param {function} [onDone]  - called when stream finishes
 * @param {function} [onError] - called on error
 */
export async function streamFetch(url, body, onToken, onDone, onError, extraHeaders = {}) {
  try {
    const response = await fetch(url, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', ...extraHeaders },
      body:    JSON.stringify(body),
    })

    if (!response.ok) {
      const text = await response.text()
      throw new Error(`HTTP ${response.status}: ${text}`)
    }

    const reader  = response.body.getReader()
    const decoder = new TextDecoder()
    let   buffer  = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() // keep partial last line

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.error) {
            onError?.(data.error)
            return
          }
          if (data.token) onToken(data.token)
          if (data.done)  onDone?.()
        } catch {
          // skip malformed chunks
        }
      }
    }
    onDone?.()
  } catch (e) {
    onError?.(e.message ?? String(e))
  }
}

/** Simple POST that returns JSON (non-streaming). */
export async function apiFetch(url, body, extraHeaders = {}) {
  const res = await fetch(url, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
    body:    JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json()
}
