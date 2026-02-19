import type { Component } from 'vue'
import {
  Home,
  Zap,
  ScrollText,
  GraduationCap,
  MessageCircle,
  Brain,
  Bot,
  Calendar,
  Mail,
  CheckSquare,
  HeartPulse,
  Timer,
  BarChart3,
  Clock,
  AlertTriangle,
  CircleCheck,
  CircleX,
  Minus,
  Hospital,
  PartyPopper,
  Square,
  Building,
  Video,
  // War Room icons
  Swords,
  Kanban,
  Tag,
  FolderOpen,
  ToggleLeft,
  ToggleRight,
  Cpu,
  Flame,
  Link,
  BookOpen,
  FileText,
  Sparkles,
  RefreshCw,
  GripVertical,
} from 'lucide-vue-next'

export const iconMap: Record<string, Component> = {
  home: Home,
  zap: Zap,
  'scroll-text': ScrollText,
  'graduation-cap': GraduationCap,
  'message-circle': MessageCircle,
  brain: Brain,
  bot: Bot,
  calendar: Calendar,
  mail: Mail,
  'check-square': CheckSquare,
  'heart-pulse': HeartPulse,
  timer: Timer,
  'bar-chart': BarChart3,
  clock: Clock,
  'alert-triangle': AlertTriangle,
  'circle-check': CircleCheck,
  'circle-x': CircleX,
  minus: Minus,
  hospital: Hospital,
  'party-popper': PartyPopper,
  square: Square,
  building: Building,
  video: Video,
  // War Room icons
  swords: Swords,
  kanban: Kanban,
  tag: Tag,
  'folder-open': FolderOpen,
  'toggle-left': ToggleLeft,
  'toggle-right': ToggleRight,
  cpu: Cpu,
  flame: Flame,
  link: Link,
  'book-open': BookOpen,
  'file-text': FileText,
  sparkles: Sparkles,
  'refresh-cw': RefreshCw,
  'grip-vertical': GripVertical,
}

export function resolveIcon(name: string): Component | null {
  return iconMap[name] ?? null
}

export function getAgentIconName(agentId: string): string {
  const lower = agentId.toLowerCase()
  if (lower.includes('matron')) return 'hospital'
  if (lower.includes('archivist')) return 'scroll-text'
  if (lower.includes('jeeves')) return 'bot'
  return 'bot'
}

export function getLevelIconName(level: string): string {
  if (level === 'info') return 'circle-check'
  if (level === 'warning') return 'alert-triangle'
  if (level === 'error') return 'circle-x'
  return 'minus'
}
