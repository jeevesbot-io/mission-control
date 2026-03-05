/**
 * Named color system — bridges CSS design tokens and component props.
 * All colors resolve to CSS variable references (never hex values).
 */

import type { CSSProperties } from 'vue'

export const NAMED_COLORS = [
  'purple', 'pink', 'green', 'blue', 'amber',
  'indigo', 'red', 'orange', 'cyan', 'yellow',
] as const

export type NamedColor = (typeof NAMED_COLORS)[number]

export function isNamedColor(value: string): value is NamedColor {
  return (NAMED_COLORS as readonly string[]).includes(value)
}

/** Returns CSS variable references for a named color */
export function getNamedColorVars(color: NamedColor | string) {
  const name = isNamedColor(color) ? color : 'indigo'
  return {
    text: `var(--mc-color-${name})`,
    bg: `var(--mc-color-${name}-bg)`,
    border: `var(--mc-color-${name}-border)`,
    accent: `var(--mc-color-${name}-accent)`,
  }
}

/** Returns inline CSSProperties for coloring an element by named color */
export function namedColorStyle(color: string): CSSProperties {
  if (!isNamedColor(color)) return {}
  const vars = getNamedColorVars(color)
  return {
    color: vars.text,
    backgroundColor: vars.bg,
    borderColor: vars.border,
  }
}

/** Stable color assignment: picks a named color from a string key */
export function colorFromKey(key: string): NamedColor {
  let hash = 0
  for (let i = 0; i < key.length; i++) {
    hash = ((hash << 5) - hash + key.charCodeAt(i)) | 0
  }
  return NAMED_COLORS[Math.abs(hash) % NAMED_COLORS.length]
}
