export function useNotification() {
  function show(message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') {
    console.log(`[${type.toUpperCase()}]`, message)
    // TODO: integrate with Naive UI n-message or n-notification
  }

  return {
    show,
  }
}
