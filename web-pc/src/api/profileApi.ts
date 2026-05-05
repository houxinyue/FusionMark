import { http } from './http'
import type {
  CopyProfilePayload,
  CreateProfilePayload,
  CurrentProfileResponse,
  DefaultProfileTemplate,
  ProfileActionResponse,
  ProfileDetail,
  ProfileSummary,
  UpdateProfilePayload,
} from '@/types/profile'

function encodeProfileId(profileId: string) {
  return encodeURIComponent(profileId)
}

export async function listProfiles(): Promise<ProfileSummary[]> {
  return http.get('/api/v1/profiles') as unknown as Promise<ProfileSummary[]>
}

export async function getCurrentProfile(): Promise<CurrentProfileResponse> {
  return http.get('/api/v1/profiles/current') as unknown as Promise<CurrentProfileResponse>
}

export async function getProfileDetail(profileId: string): Promise<ProfileDetail> {
  return http.get(`/api/v1/profiles/${encodeProfileId(profileId)}`) as unknown as Promise<ProfileDetail>
}

export async function createProfile(payload: CreateProfilePayload): Promise<ProfileDetail> {
  return http.post('/api/v1/profiles', payload) as unknown as Promise<ProfileDetail>
}

export async function updateProfile(
  profileId: string,
  payload: UpdateProfilePayload,
): Promise<ProfileDetail> {
  return http.put(`/api/v1/profiles/${encodeProfileId(profileId)}`, payload) as unknown as Promise<ProfileDetail>
}

export async function copyProfile(
  profileId: string,
  payload: CopyProfilePayload,
): Promise<ProfileDetail> {
  return http.post(`/api/v1/profiles/${encodeProfileId(profileId)}/copy`, payload) as unknown as Promise<ProfileDetail>
}

export async function activateProfile(profileId: string): Promise<ProfileActionResponse> {
  return http.post(`/api/v1/profiles/${encodeProfileId(profileId)}/activate`) as unknown as Promise<ProfileActionResponse>
}

export async function deleteProfile(profileId: string): Promise<ProfileActionResponse> {
  return http.delete(`/api/v1/profiles/${encodeProfileId(profileId)}`) as unknown as Promise<ProfileActionResponse>
}

export async function getDefaultProfileTemplate(): Promise<DefaultProfileTemplate> {
  return http.get('/api/v1/config/default') as unknown as Promise<DefaultProfileTemplate>
}

export function getProfileDownloadUrl(profileId: string) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  return `${baseUrl}/api/v1/profiles/${encodeProfileId(profileId)}/download`
}
