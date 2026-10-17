import { randomUUID } from 'node:crypto'
import { BedrockAgentCoreClient, InvokeAgentRuntimeCommand } from '@aws-sdk/client-bedrock-agentcore'

// ponytail: in-memory rate limit, per Nitro instance. Enough for one room; move to a KV store
// if this ever outlives the talk.
const runs = new Map<string, number>()

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const { demo, guard } = await readBody<{ demo?: string; guard?: boolean }>(event)
  const replay = isReplay(event)

  if (!demo || !/^0[0-4]$/.test(demo)) {
    throw createError({ statusCode: 400, statusMessage: 'demo must be one of 00..04' })
  }

  // Replay streams a hand-written fixture: no model, no AWS, no run limit.
  if (replay) {
    setResponseHeaders(event, {
      'content-type': 'text/event-stream',
      'cache-control': 'no-cache',
      'x-accel-buffering': 'no',
    })
    return replayStream(demo, guard !== false)
  }

  // AgentCore requires a session id of at least 33 chars; one per visitor keeps each
  // attendee's run isolated in its own microVM.
  let sessionId = getCookie(event, 'agent_session')
  if (!sessionId || sessionId.length < 33) {
    sessionId = `demo-${randomUUID()}-${randomUUID()}`.slice(0, 64)
    setCookie(event, 'agent_session', sessionId, { httpOnly: true, sameSite: 'lax', maxAge: 86400 })
  }

  const used = runs.get(sessionId) ?? 0
  if (used >= Number(config.maxRunsPerVisitor)) {
    throw createError({ statusCode: 429, statusMessage: 'Limite de ejecuciones alcanzado.' })
  }
  runs.set(sessionId, used + 1)

  const payload = JSON.stringify({ demo, guard: guard !== false })
  const upstream = config.agentRuntimeArn
    ? await invokeAgentCore(config.agentRuntimeArn, config.awsRegion, sessionId, payload)
    : await invokeLocal(config.localAgentUrl, sessionId, payload)

  setResponseHeaders(event, {
    'content-type': 'text/event-stream',
    'cache-control': 'no-cache',
    'x-accel-buffering': 'no',
  })
  return upstream
})

// NUXT_REPLAY=1 (server env) or ?replay=1 on the request turns replay on.
// Nuxt parses env values, so NUXT_REPLAY=1 arrives as the number 1: compare as a string.
function isReplay(event: Parameters<typeof getQuery>[0]) {
  const config = useRuntimeConfig()
  return String(config.replay) === '1' || String(config.public.replay) === '1' || getQuery(event).replay === '1'
}

async function invokeAgentCore(arn: string, region: string, sessionId: string, payload: string) {
  const client = new BedrockAgentCoreClient({ region })
  const response = await client.send(new InvokeAgentRuntimeCommand({
    agentRuntimeArn: arn,
    runtimeSessionId: sessionId,
    qualifier: 'DEFAULT',
    payload: Buffer.from(payload),
  }))
  // The runtime streams SSE back; hand the bytes straight to the browser.
  return response.response as ReadableStream
}

async function invokeLocal(url: string, sessionId: string, payload: string) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId,
    },
    body: payload,
  })
  if (!response.ok || !response.body) {
    throw createError({
      statusCode: 502,
      statusMessage: `El agente local no respondio (${response.status}). Corre "python app.py" en backend/.`,
    })
  }
  return response.body
}
