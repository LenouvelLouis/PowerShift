/**
 * Color palette and icon mapping for energy assets.
 * Generator colors are assigned by name keyword, with fallback to palette rotation.
 */

export const PALETTE = ['#3C83F8', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#F97316', '#84CC16']

export function generatorColor(name: string, index: number): string {
  const n = name.toLowerCase()
  if (n.includes('wind')) return '#3C83F8'
  if (n.includes('solar') || n.includes('pv')) return '#F59E0B'
  if (n.includes('nuclear')) return '#8B5CF6'
  return PALETTE[index % PALETTE.length] as string
}

export function generatorIcon(name: string): string {
  const n = name.toLowerCase()
  if (n.includes('wind')) return 'i-heroicons-arrow-path'
  if (n.includes('solar') || n.includes('pv')) return 'i-heroicons-sun'
  if (n.includes('nuclear')) return 'i-heroicons-bolt'
  if (n.includes('house') || n.includes('residential')) return 'i-heroicons-home'
  if (n.includes('ev') || n.includes('vehicle')) return 'i-heroicons-truck'
  if (n.includes('cable')) return 'i-heroicons-link'
  if (n.includes('transformer')) return 'i-heroicons-cpu-chip'
  return 'i-heroicons-bolt'
}
