# WebSocket Protocol — Interview Copilot

## Connection

```
ws://localhost:8000/ws/interview/{session_id}?token={jwt_token}
```

## Message Format

All messages use JSON with a `type` field discriminator.

### Client → Server

```json
{ "type": "...", "payload": {...}, "request_id": "uuid" }
```

### Server → Client

```json
{ "type": "...", "payload": {...}, "request_id": "uuid?", "timestamp": "ISO8601" }
```

## Client Events

| Type | Payload | Description |
|------|---------|-------------|
| `client.hello` | `{ client_version, platform }` | Handshake |
| `audio.chunk` | `{ data: base64, format: "pcm_s16le", sample_rate: 16000 }` | Raw audio chunk |
| `audio.stop` | `{}` | End of audio stream |
| `screen.frame` | `{ data: base64, width, height, timestamp }` | Screen capture frame |
| `screen.stop` | `{}` | Stop screen capture |
| `answer.feedback` | `{ answer_id, rating, comment? }` | User feedback on answer |
| `mode.switch` | `{ mode: "quick"|"interview"|"senior"|"coding"|"scenario" }` | Change answer mode |
| `interrupt` | `{}` | Cancel current generation |
| `controls.pause` | `{}` | Pause processing |
| `controls.resume` | `{}` | Resume processing |

## Server Events

| Type | Payload | Description |
|------|---------|-------------|
| `server.hello` | `{ session_id, server_version }` | Connection confirmed |
| `pipeline.status` | `{ stage, message }` | Processing stage update |
| `transcription.partial` | `{ text, confidence, speaker? }` | Partial transcript |
| `transcription.final` | `{ text, confidence, speaker?, duration_ms }` | Final transcript segment |
| `question.detected` | `{ question_id, text, category, classification }` | Question identified |
| `answer.delta` | `{ answer_id, token, index }` | Streaming answer token |
| `answer.done` | `{ answer_id, full_text, mode, sources? }` | Answer complete |
| `sources.updated` | `{ answer_id, sources: [...] }` | Retrieved sources |
| `code.delta` | `{ answer_id, language, token, index }` | Streaming code token |
| `code.done` | `{ answer_id, code, test_results? }` | Code generation complete |
| `error` | `{ code, message, recoverable }` | Error event |
| `pong` | `{}` | Heartbeat response |

## Pipeline Stages

```
listening → transcribing → detecting → classifying → retrieving → thinking → validating → answering
```

## Heartbeat

Server sends `ping` every 30s. Client must respond with `pong` within 10s or connection is terminated.

## Reconnection

Client should reconnect with exponential backoff:
- Attempt 1: 1s
- Attempt 2: 2s
- Attempt 3: 4s
- Max: 30s

On reconnect, send `client.hello` with last received `request_id` to resume.
