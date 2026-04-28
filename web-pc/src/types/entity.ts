export interface EntityColorConfig {
  bg: string
  text: string
  label: string
}

export interface ExtractedEntity {
  text: string
  type: string
  char_start?: number | null
  char_end?: number | null
}
