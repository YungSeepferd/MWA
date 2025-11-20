/**
 * Mock data service for testing the Market Intelligence app
 * Provides realistic mock data that matches the API response structure
 */

import type {
  MarketIntelligenceContact,
  ContactListResponse,
  MarketIntelligenceAnalytics,
  ApiResponse,
  ContactScoringResponse
} from '../types/api';

// Mock contacts data
const mockContacts: MarketIntelligenceContact[] = [
  {
    id: '1',
    name: 'Maximilian Schmidt',
    email: 'max.schmidt@immobilien-muenchen.de',
    phone: '+49 89 12345678',
    position: 'Property Manager',
    company_name: 'Schmidt Immobilien GmbH',
    agency_type: 'property_manager',
    market_areas: ['München Zentrum', 'Schwabing'],
    business_context: {
      property_count: 45,
      portfolio_value: 12000000,
      years_experience: 8,
      specialization: 'Luxury apartments'
    },
    outreach_history: [
      {
        date: '2024-01-15T10:30:00Z',
        type: 'email',
        status: 'responded',
        notes: 'Interested in collaboration'
      }
    ],
    confidence_score: 0.85,
    quality_score: 0.92,
    lead_source: 'manual_entry',
    extraction_metadata: {
      source: 'business_card',
      confidence: 0.95,
      timestamp: '2024-01-10T14:22:00Z'
    },
    created_at: '2024-01-10T14:22:00Z',
    updated_at: '2024-01-15T10:30:00Z',
    status: 'approved'
  },
  {
    id: '2',
    name: 'Anna Müller',
    email: 'anna.mueller@wg-gesucht-consulting.de',
    phone: '+49 89 98765432',
    position: 'Real Estate Agent',
    company_name: 'WG Gesucht Consulting',
    agency_type: 'real_estate_agent',
    market_areas: ['München Ost', 'Giesing'],
    business_context: {
      property_count: 120,
      portfolio_value: 8500000,
      years_experience: 5,
      specialization: 'Student apartments'
    },
    outreach_history: [
      {
        date: '2024-01-12T09:15:00Z',
        type: 'phone',
        status: 'no_response',
        notes: 'Left voicemail'
      }
    ],
    confidence_score: 0.72,
    quality_score: 0.88,
    lead_source: 'web_scraping',
    extraction_metadata: {
      source: 'website',
      confidence: 0.90,
      timestamp: '2024-01-08T11:45:00Z'
    },
    created_at: '2024-01-08T11:45:00Z',
    updated_at: '2024-01-12T09:15:00Z',
    status: 'pending'
  },
  {
    id: '3',
    name: 'Thomas Weber',
    email: 'thomas.weber@hausverwaltung-bayern.de',
    phone: '+49 89 55512345',
    position: 'Building Manager',
    company_name: 'Hausverwaltung Bayern',
    agency_type: 'landlord',
    market_areas: ['München Süd', 'Sendling'],
    business_context: {
      property_count: 25,
      portfolio_value: 5000000,
      years_experience: 12,
      specialization: 'Commercial properties'
    },
    outreach_history: [
      {
        date: '2024-01-14T16:20:00Z',
        type: 'email',
        status: 'responded',
        notes: 'Scheduled meeting for next week'
      }
    ],
    confidence_score: 0.78,
    quality_score: 0.85,
    lead_source: 'manual_entry',
    extraction_metadata: {
      source: 'business_card',
      confidence: 0.88,
      timestamp: '2024-01-09T13:10:00Z'
    },
    created_at: '2024-01-09T13:10:00Z',
    updated_at: '2024-01-14T16:20:00Z',
    status: 'approved'
  }
];

// Mock analytics data
const mockAnalytics: MarketIntelligenceAnalytics = {
  total_contacts: 156,
  approved_contacts: 89,
  pending_contacts: 42,
  rejected_contacts: 25,
  average_confidence_score: 0.76,
  average_quality_score: 0.82,
  outreach_success_rate: 0.65,
  contact_distribution: {
    property_manager: 45,
    real_estate_agent: 67,
    landlord: 32,
    other: 12
  },
  market_area_coverage: {
    'München Zentrum': 23,
    'Schwabing': 18,
    'München Ost': 15,
    'Giesing': 12,
    'München Süd': 20,
    'Sendling': 14,
    'Other': 54
  },
  monthly_trends: [
    { month: 'Jan 2024', new_contacts: 15, outreach_success: 0.62 },
    { month: 'Dec 2023', new_contacts: 12, outreach_success: 0.58 },
    { month: 'Nov 2023', new_contacts: 18, outreach_success: 0.71 },
    { month: 'Oct 2023', new_contacts: 14, outreach_success: 0.65 }
  ]
};

// Mock scoring data
const mockScoring: ContactScoringResponse = {
  overall_score: 0.85,
  breakdown: {
    business_context: { score: 0.90, weight: 0.4 },
    market_relevance: { score: 0.85, weight: 0.2 },
    engagement: { score: 0.80, weight: 0.15 },
    data_completeness: { score: 0.95, weight: 0.1 },
    source_reliability: { score: 0.75, weight: 0.05 }
  },
  recommendations: [
    'Consider follow-up outreach in 2 weeks',
    'High potential for collaboration',
    'Strong market presence in target areas'
  ]
};

class MockDataService {
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async getContacts(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
  }): Promise<ApiResponse<ContactListResponse>> {
    await this.delay(500); // Simulate network delay
    
    let filteredContacts = [...mockContacts];
    
    // Apply search filter
    if (params?.search) {
      const searchTerm = params.search.toLowerCase();
      filteredContacts = filteredContacts.filter(contact =>
        contact.name.toLowerCase().includes(searchTerm) ||
        contact.company_name.toLowerCase().includes(searchTerm) ||
        contact.email.toLowerCase().includes(searchTerm)
      );
    }
    
    // Apply pagination
    const page = params?.page || 1;
    const pageSize = params?.pageSize || 20;
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedContacts = filteredContacts.slice(startIndex, endIndex);
    
    return {
      data: {
        contacts: paginatedContacts,
        total_count: filteredContacts.length,
        page,
        page_size: pageSize,
        total_pages: Math.ceil(filteredContacts.length / pageSize)
      },
      success: true,
      message: 'Contacts retrieved successfully'
    };
  }

  async getContact(id: string): Promise<ApiResponse<MarketIntelligenceContact>> {
    await this.delay(300);
    
    const contact = mockContacts.find(c => c.id === id);
    
    if (!contact) {
      throw new Error(`Contact with id ${id} not found`);
    }
    
    return {
      data: contact,
      success: true,
      message: 'Contact retrieved successfully'
    };
  }

  async getAnalytics(): Promise<ApiResponse<MarketIntelligenceAnalytics>> {
    await this.delay(400);
    
    return {
      data: mockAnalytics,
      success: true,
      message: 'Analytics data retrieved successfully'
    };
  }

  async getContactScoring(id: string): Promise<ApiResponse<ContactScoringResponse>> {
    await this.delay(350);
    
    return {
      data: mockScoring,
      success: true,
      message: 'Scoring data retrieved successfully'
    };
  }

  // Simulate WebSocket messages
  generateMockWebSocketMessage(): any {
    const messageTypes = [
      'contact_created',
      'contact_updated',
      'contact_approved',
      'contact_rejected'
    ];
    
    const type = messageTypes[Math.floor(Math.random() * messageTypes.length)];
    const contact = mockContacts[Math.floor(Math.random() * mockContacts.length)];
    
    return {
      type,
      data: { contact },
      timestamp: new Date().toISOString()
    };
  }
}

export const mockDataService = new MockDataService();
export { mockContacts, mockAnalytics, mockScoring };