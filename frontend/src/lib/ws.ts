import type { WsServerEvent, WsClientEvent } from "@/types";

type EventHandler = (event: WsServerEvent) => void;

export class InterviewWebSocket {
  private ws: WebSocket | null = null;
  private handlers: EventHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnects = 15;
  private baseDelayMs = 1000;
  private url: string;
  private connected = false;

  constructor(sessionId: string, baseUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000") {
    this.url = `${baseUrl}/ws/interview/${sessionId}`;
  }

  connect(): void {
    if (this.connected) return;
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => {
        this.connected = true;
        this.reconnectAttempts = 0;
        this.send({ type: "client.hello", payload: { client_version: "0.1.0", platform: "web" } });
      };
      this.ws.onmessage = (msg) => {
        try {
          const event = JSON.parse(msg.data) as WsServerEvent;
          this.handlers.forEach((h) => h(event));
        } catch {
          /* ignore malformed */
        }
      };
      this.ws.onclose = () => {
        this.connected = false;
        this.reconnect();
      };
      this.ws.onerror = () => {
        this.connected = false;
      };
    } catch {
      this.reconnect();
    }
  }

  onEvent(handler: EventHandler): () => void {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler);
    };
  }

  send(event: WsClientEvent): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(event));
    }
  }

  sendAudioChunk(base64Data: string, sampleRate = 16000): void {
    this.send({
      type: "audio.chunk",
      payload: { data: base64Data, format: "pcm_s16le", sample_rate: sampleRate },
    });
  }

  stopAudio(): void {
    this.send({ type: "audio.stop", payload: {} });
  }

  switchMode(mode: string): void {
    this.send({ type: "mode.switch", payload: { mode } });
  }

  interrupt(): void {
    this.send({ type: "interrupt", payload: {} });
  }

  sendFeedback(answerId: string, rating: number, comment?: string): void {
    this.send({
      type: "answer.feedback",
      payload: { answer_id: answerId, rating, comment },
    });
  }

  disconnect(): void {
    this.connected = false;
    this.ws?.close();
  }

  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnects) return;
    const delay = this.baseDelayMs * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts += 1;
    setTimeout(() => this.connect(), Math.min(delay, 30000));
  }
}
