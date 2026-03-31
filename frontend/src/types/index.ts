export interface ResourceInfo {
  name: string;
  category: string;
  description: string;
  phone?: string;
  url?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  resources?: ResourceInfo[];
  isCrisis?: boolean;
  isStreaming?: boolean;
  timestamp: Date;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  resources: ResourceInfo[];
  crisis?: {
    is_crisis: boolean;
    tier: number;
    message: string;
  };
}

export interface IntakeResponse {
  intake_id: string;
  state: string;
  message: string;
  is_complete: boolean;
  summary?: string;
}

export interface AnalyticsOverview {
  total_sessions: number;
  messages_today: number;
  unique_users_7d: number;
  crisis_alerts: number;
}

export interface TopQuestion {
  question: string;
  count: number;
}

export interface TopResource {
  name: string;
  citations: number;
  clicks: number;
}

export interface UsageTrendPoint {
  date: string;
  sessions: number;
  messages: number;
}

export interface AnalyticsDashboard {
  overview: AnalyticsOverview;
  top_questions: TopQuestion[];
  top_resources: TopResource[];
  usage_trend: UsageTrendPoint[];
}

export interface KnowledgeDocument {
  id: number;
  title: string;
  category: string;
  content: string;
  url?: string;
  phone?: string;
  source: string;
  chunks_count: number;
  created_at: string;
  updated_at: string;
}

export interface UserInfo {
  id: number;
  username: string;
  full_name?: string;
  role: string;
}
