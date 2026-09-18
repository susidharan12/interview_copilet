import { useEffect, useRef, type MutableRefObject } from "react";
import { useAppStore } from "@/store/useAppStore";
import { InterviewWebSocket } from "@/lib/ws";
import type { WsServerEvent } from "@/types";

type Payload = Record<string, any>;

const DEFAULT_CLASSIFICATION = {
  category: "unknown",
  technology: null,
  difficulty: null,
  requires_retrieval: false,
  requires_reasoning: false,
  requires_code_execution: false,
  requires_screen_context: false,
  confidence: 0,
};

export function useInterviewSocket(): MutableRefObject<InterviewWebSocket | null> {
  const session = useAppStore((s) => s.session);
  const wsRef = useRef<InterviewWebSocket | null>(null);

  useEffect(() => {
    if (!session) return;

    const ws = new InterviewWebSocket(session.id);
    wsRef.current = ws;

    const dispatch = (ev: WsServerEvent) => {
      const st = useAppStore.getState();
      const p = (ev.payload ?? {}) as Payload;

      switch (ev.type) {
        case "pipeline.status":
          st.setPipelineStatus({ stage: p.stage, message: p.message });
          break;
        case "transcription.partial":
          st.addTranscription({
            text: p.text,
            confidence: p.confidence ?? 0,
            speaker: p.speaker,
            is_final: false,
            timestamp: Date.now(),
          });
          break;
        case "transcription.final":
          st.addTranscription({
            text: p.text,
            confidence: p.confidence ?? 1,
            speaker: p.speaker,
            is_final: true,
            timestamp: Date.now(),
          });
          break;
        case "question.detected":
          st.setCurrentQuestion({
            question_id: p.question_id,
            text: p.text,
            category: p.category ?? "unknown",
            classification: p.classification ?? DEFAULT_CLASSIFICATION,
            confidence: p.confidence ?? 0,
          });
          break;
        case "answer.delta":
          st.setIsGenerating(true);
          st.appendAnswerToken(p.token ?? "");
          break;
        case "answer.done":
          st.setAnswerDone({
            answer_id: p.answer_id,
            full_text: p.full_text,
            mode: p.mode,
            sources: p.sources ?? [],
            validation: p.validation ?? null,
            latency_ms: p.latency_ms ?? 0,
          });
          break;
        case "sources.updated":
          if (p.sources) st.setSources(p.sources);
          break;
        case "error":
          st.setError(p.message ?? "Unknown error");
          break;
      }
    };

    ws.onEvent(dispatch);
    ws.connect();

    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
  }, [session?.id]);

  return wsRef;
}

function bytesToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]!);
  return btoa(binary);
}

export function useMicCapture(active: boolean, wsRef: MutableRefObject<InterviewWebSocket | null>): void {
  useEffect(() => {
    if (!active) return;

    let stream: MediaStream | null = null;
    let ctx: AudioContext | null = null;
    let proc: ScriptProcessorNode | null = null;
    let src: MediaStreamAudioSourceNode | null = null;
    let stopped = false;

    async function start() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 },
        });
        if (stopped) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        ctx = new AudioContext({ sampleRate: 16000 });
        src = ctx.createMediaStreamSource(stream);
        proc = ctx.createScriptProcessor(4096, 1, 1);
        proc.onaudioprocess = (e) => {
          const ws = wsRef.current;
          if (!ws) return;
          const input = e.inputBuffer.getChannelData(0);
          const pcm = new Int16Array(input.length);
          for (let i = 0; i < input.length; i++) {
            const s = Math.max(-1, Math.min(1, input[i]!));
            pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
          }
          ws.sendAudioChunk(bytesToBase64(pcm.buffer));
        };
        src.connect(proc);
        proc.connect(ctx.destination);
        useAppStore.getState().setError(null);
      } catch {
        useAppStore.getState().setError("Mic access denied — allow microphone to listen");
      }
    }

    start();

    return () => {
      stopped = true;
      try {
        proc?.disconnect();
        src?.disconnect();
        void ctx?.close();
      } catch {
        /* ignore */
      }
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [active, wsRef]);
}