export const logger = {
  info: (msg: string, meta?: any) => console.log(`[INFO] ${new Date().toISOString()} - ${msg}`, meta || ''),
  error: (msg: string, err?: any) => console.error(`[ERROR] ${new Date().toISOString()} - ${msg}`, err || ''),
  audit: (action: string, actor: string) => console.log(`[AUDIT] ${action} by ${actor}`)
};