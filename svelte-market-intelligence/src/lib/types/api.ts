// Market Intelligence Contact Types
export interface MarketIntelligenceContact {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  position?: string;
  company_name?: string;
  agency_type?: AgencyType;
  market_areas?: MarketArea[];
  outreach_history?: OutreachHistory[];
  confidence_score?: number;
  quality_score?: number;
  lead_source?: string;
  extraction_method?: string;
  business_context?: BusinessContext;
  created_at: string;
  updated_at: string;
  is_approved?: boolean;
  is_rejected?: boolean;
  rejection_reason?: string;
  notes?: string;
}

export enum AgencyType {
  PROPERTY_MANAGER = 'property_manager',
  LANDLORD = 'landlord',
  REAL_ESTATE_AGENT = 'real_estate_agent',
  BROKER = 'broker',
  DEVELOPER = 'developer',
  OTHER = 'other'
}

export interface MarketArea {
  name: string;
  relevance_score: number;
  is_primary: boolean;
  geographic_focus?: string;
}

export interface OutreachHistory {
  date: string;
  method: OutreachMethod;
  outcome: OutreachOutcome;
  notes?: string;
  follow_up_required: boolean;
  follow_up_date?: string;
}

export enum OutreachMethod {
  EMAIL = 'email',
  PHONE = 'phone',
  IN_PERSON = 'in_person',
  SOCIAL_MEDIA = 'social_media',
  OTHER = 'other'
}

export enum OutreachOutcome {
  SUCCESSFUL = 'successful',
  NO_RESPONSE = 'no_response',
  REJECTED = 'rejected',
  FOLLOW_UP_SCHEDULED = 'follow_up_scheduled',
  OTHER = 'other'
}

export interface BusinessContext {
  company_size?: CompanySize;
  portfolio_size?: number;
  specialization?: string;
  market_focus?: string;
  years_in_business?: number;
  reputation_score?: number;
}

export enum CompanySize {
  SMALL = 'small',
  MEDIUM = 'medium',
  LARGE = 'large',
  ENTERPRISE = 'enterprise'
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    page_size: number;
    total_pages: number;
    total_items: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface ContactListResponse extends PaginatedResponse<MarketIntelligenceContact> {}

export interface ContactCreateRequest {
  name: string;
  email?: string;
  phone?: string;
  position?: string;
  company_name?: string;
  agency_type?: AgencyType;
  market_areas?: Omit<MarketArea, 'relevance_score'>[];
  lead_source?: string;
  extraction_method?: string;
  business_context?: Omit<BusinessContext, 'reputation_score'>;
  notes?: string;
}

export interface ContactUpdateRequest extends Partial<ContactCreateRequest> {
  id: string;
  is_approved?: boolean;
  is_rejected?: boolean;
  rejection_reason?: string;
}

export interface ContactScoringResponse {
  contact_id: string;
  overall_score: number;
  breakdown: {
    business_context: number;
    market_relevance: number;
    engagement: number;
    data_completeness: number;
    source_reliability: number;
  };
  recommendations: string[];
}

// Analytics Types
export interface MarketIntelligenceAnalytics {
  total_contacts: number;
  approved_contacts: number;
  rejected_contacts: number;
  pending_contacts: number;
  average_confidence_score: number;
  average_quality_score: number;
  agency_type_distribution: Record<AgencyType, number>;
  market_area_distribution: Record<string, number>;
  outreach_success_rate: number;
  monthly_trends: MonthlyTrend[];
}

export interface MonthlyTrend {
  month: string;
  contacts_added: number;
  contacts_approved: number;
  average_score: number;
}

// WebSocket Types
export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
  timestamp: string;
}

export enum WebSocketMessageType {
  CONTACT_CREATED = 'contact_created',
  CONTACT_UPDATED = 'contact_updated',
  CONTACT_DELETED = 'contact_deleted',
  CONTACT_APPROVED = 'contact_approved',
  CONTACT_REJECTED = 'contact_rejected',
  ANALYTICS_UPDATED = 'analytics_updated',
  SYSTEM_NOTIFICATION = 'system_notification'
}

// Error Types
export interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

// Search and Filter Types
export interface ContactFilter {
  agency_type?: AgencyType;
  market_area?: string;
  min_confidence_score?: number;
  min_quality_score?: number;
  is_approved?: boolean;
  is_rejected?: boolean;
  lead_source?: string;
  date_range?: {
    start: string;
    end: string;
  };
}

export interface ContactSearchRequest {
  query?: string;
  filters?: ContactFilter;
  pagination?: {
    page: number;
    page_size: number;
  };
  sort?: {
    field: string;
    direction: 'asc' | 'desc';
  };
}

// Export Types
export interface ExportRequest {
  format: 'csv' | 'json' | 'pdf';
  filters?: ContactFilter;
  include_fields: string[];
}

export interface ExportResponse {
  export_id: string;
  status: 'processing' | 'completed' | 'failed';
  download_url?: string;
  estimated_completion_time?: string;
}

// Utility Types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type Required<T, K extends keyof T> = T & Required<Pick<T, K>>;