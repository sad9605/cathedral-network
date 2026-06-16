export const tracer = {
  startSpan: (name: string) => ({ end: () => console.log(`[TRACE] End span: ${name}`) }),
  trackTool: (name: string, args: any) => console.log(`[TRACE] Tool: ${name}`, args)
};