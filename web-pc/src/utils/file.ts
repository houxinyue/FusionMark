export function isPdfFile(file: File): boolean {
  return file.type === 'application/pdf'
}

export function createObjectUrl(file: File): string {
  return URL.createObjectURL(file)
}

export function revokeObjectUrl(url: string): void {
  URL.revokeObjectURL(url)
}
