import { http } from './http'
import type {
  CopilotMessagePayload,
  CopilotSessionResponse,
  CopilotValidatePayload,
} from '@/types/profileCopilot'

function encodeSessionId(sessionId: string) {
  return encodeURIComponent(sessionId)
}

export async function createCopilotSession(): Promise<CopilotSessionResponse> {
  return http.post('/api/v1/profile-copilot/sessions') as unknown as Promise<CopilotSessionResponse>
}

export async function getCopilotSession(sessionId: string): Promise<CopilotSessionResponse> {
  return http.get(`/api/v1/profile-copilot/sessions/${encodeSessionId(sessionId)}`) as unknown as Promise<CopilotSessionResponse>
}

export async function sendCopilotMessage(
  sessionId: string,
  payload: CopilotMessagePayload,
): Promise<CopilotSessionResponse> {
  return http.post(
    `/api/v1/profile-copilot/sessions/${encodeSessionId(sessionId)}/messages`,
    payload,
  ) as unknown as Promise<CopilotSessionResponse>
}

export async function validateCopilotDraft(
  sessionId: string,
  payload: CopilotValidatePayload,
): Promise<CopilotSessionResponse> {
  return http.post(
    `/api/v1/profile-copilot/sessions/${encodeSessionId(sessionId)}/validate`,
    payload,
  ) as unknown as Promise<CopilotSessionResponse>
}

