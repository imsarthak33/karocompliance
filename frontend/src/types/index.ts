/**
 * Domain type definitions for KaroCompliance.
 *
 * Strict Mandates:
 *   • NO `: any` anywhere
 *   • All types match backend Pydantic response models exactly
 */

// ---------------------------------------------------------------------------
// Auth & Tenant
// ---------------------------------------------------------------------------
export interface IUser {
  id: string;
  email: string;
  created_at?: string;
}

export interface ISession {
  access_token: string;
  refresh_token?: string;
  expires_at?: number;
  user: IUser;
}

export interface ICAFirm {
  id: string;
  firm_name: string;
  ca_name: string;
  email: string;
  phone: string;
  icai_membership_number?: string | null;
  whatsapp_number_assigned?: string | null;
  gstin?: string | null;
  subscription_plan?: 'trial' | 'starter' | 'professional' | 'enterprise' | null;
  trial_ends_at?: string | null;
  is_active?: boolean;
  onboarding_completed?: boolean;
  created_at?: string | null;
}

// ---------------------------------------------------------------------------
// Clients
// ---------------------------------------------------------------------------
export interface IClient {
  id: string;
  ca_firm_id: string;
  client_name: string;
  gstin: string;
  trade_name?: string | null;
  phone_whatsapp: string;
  email?: string | null;
  filing_frequency?: 'monthly' | 'quarterly' | null;
  gst_registration_type?: 'regular' | 'composition' | 'exempt' | null;
  state_code?: string | null;
  is_active?: boolean;
  last_document_received_at?: string | null;
  last_filed_at?: string | null;
  onboarded_to_whatsapp?: boolean;
  created_at?: string | null;
}

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------
export type DocumentType =
  | 'purchase_invoice'
  | 'sale_invoice'
  | 'bank_statement'
  | 'credit_note'
  | 'debit_note'
  | 'voice_note'
  | 'unknown';

export type ProcessingStatus =
  | 'received'
  | 'queued'
  | 'processing'
  | 'extracted'
  | 'reconciled'
  | 'failed'
  | 'flagged';

export interface IDocument {
  id: string;
  ca_firm_id: string;
  client_id: string;
  whatsapp_message_id?: string | null;
  document_type?: DocumentType | null;
  original_file_name?: string | null;
  storage_key: string;
  file_format?: 'pdf' | 'image' | 'excel' | 'audio' | 'unknown' | null;
  processing_status?: ProcessingStatus | null;
  processing_error?: string | null;
  confidence_score?: string | null; // Decimal serialized as string
  requires_manual_review?: boolean;
  review_reason?: string | null;
  received_at?: string | null;
  processed_at?: string | null;
}

// ---------------------------------------------------------------------------
// Anomalies
// ---------------------------------------------------------------------------
export type AnomalyType =
  | 'itc_mismatch'
  | 'missing_invoice'
  | 'duplicate_invoice'
  | 'rate_mismatch'
  | 'supplier_non_filer'
  | 'data_quality'
  | 'deadline_risk'
  | 'high_value_transaction';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export interface IAnomaly {
  id: string;
  client_id: string;
  ca_firm_id: string;
  anomaly_type: AnomalyType;
  severity: Severity;
  description: string;
  suggested_action?: string | null;
  is_resolved: boolean;
  created_at?: string | null;
}

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------
export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface INotification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  timestamp: number;
}

// ---------------------------------------------------------------------------
// WebSocket Events
// ---------------------------------------------------------------------------
export type WebSocketEventType =
  | 'document_received'
  | 'document_processed'
  | 'anomaly_detected'
  | 'agent_status';

export interface IWebSocketEvent {
  event: WebSocketEventType;
  document_id?: string;
  client_name?: string;
  anomaly?: IAnomaly;
  status?: string;
  timestamp?: string;
}

// ---------------------------------------------------------------------------
// API Responses
// ---------------------------------------------------------------------------
export interface IWebhookResponse {
  status: string;
}

export interface ISubscriptionResponse {
  subscription_id: string;
  short_url?: string | null;
}
