// Preserve the existing employee allowlist; visitor login never uses this gate.
export const allowedEmails = [
  'g99226@gmail.com',
  'chenhongrui416@gmail.com',
  'p124826960@gmail.com',
  '44o3249@gmaiil.com',
  'xindongh522@gmail.com',
]

export function isAllowedMember(email) {
  return allowedEmails.includes(email?.trim().toLowerCase())
}
