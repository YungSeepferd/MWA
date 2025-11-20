import { writable, derived } from 'svelte/store';
import { apiClient } from '$lib/services/api';
import type { MarketIntelligenceContact, ContactListResponse, AgencyType } from '$lib/types/api';

interface ContactFilters {
  search: string;
  agencyType: string;
  confidence: string;
  status: string;
}

interface ContactSort {
  field: string;
  order: 'asc' | 'desc';
}

interface ContactState {
  contacts: MarketIntelligenceContact[];
  filteredContacts: MarketIntelligenceContact[];
  selectedContacts: Set<string>;
  currentPage: number;
  itemsPerPage: number;
  filters: ContactFilters;
  sort: ContactSort;
  isLoading: boolean;
  error: string | null;
}

const initialState: ContactState = {
  contacts: [],
  filteredContacts: [],
  selectedContacts: new Set(),
  currentPage: 1,
  itemsPerPage: 20,
  filters: {
    search: '',
    agencyType: '',
    confidence: '',
    status: ''
  },
  sort: {
    field: 'created_at',
    order: 'desc'
  },
  isLoading: false,
  error: null
};

export const contactStore = writable<ContactState>(initialState);

export const loadContacts = async (params?: {
  page?: number;
  pageSize?: number;
  search?: string;
}) => {
  contactStore.update(store => ({ ...store, isLoading: true, error: null }));

  try {
    const response: ContactListResponse = await apiClient.getContacts(params);
    
    contactStore.update(store => ({
      ...store,
      contacts: response.data || [],
      filteredContacts: response.data || [],
      currentPage: params?.page || 1,
      isLoading: false,
      error: null
    }));
  } catch (error) {
    console.error('Failed to load contacts:', error);
    contactStore.update(store => ({
      ...store,
      isLoading: false,
      error: error instanceof Error ? error.message : 'Failed to load contacts'
    }));
  }
};

export const applyFilters = (newFilters: Partial<ContactFilters>) => {
  contactStore.update(store => {
    const filters = { ...store.filters, ...newFilters };
    const filteredContacts = store.contacts.filter(contact => {
      // Agency Type filter
      if (filters.agencyType && contact.agency_type !== filters.agencyType) {
        return false;
      }

      // Status filter
      if (filters.status) {
        if (filters.status === 'approved' && !contact.is_approved) return false;
        if (filters.status === 'rejected' && !contact.is_rejected) return false;
        if (filters.status === 'pending' && (contact.is_approved || contact.is_rejected)) return false;
      }

      // Confidence filter
      if (filters.confidence) {
        const confidence = contact.confidence_score || 0;
        switch (filters.confidence) {
          case 'high':
            if (confidence < 0.9) return false;
            break;
          case 'medium':
            if (confidence < 0.7 || confidence >= 0.9) return false;
            break;
          case 'low':
            if (confidence >= 0.7) return false;
            break;
        }
      }

      // Search filter
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        const searchableText = `${contact.name} ${contact.email} ${contact.phone} ${contact.company_name} ${contact.position}`.toLowerCase();
        if (!searchableText.includes(searchTerm)) {
          return false;
        }
      }

      return true;
    });

    return {
      ...store,
      filters,
      filteredContacts,
      currentPage: 1,
      selectedContacts: new Set() // Clear selections when filters change
    };
  });
};

export const sortContacts = (field: string, order: 'asc' | 'desc' = 'desc') => {
  contactStore.update(store => {
    const sortedContacts = [...store.filteredContacts].sort((a, b) => {
      let aValue = a[field as keyof MarketIntelligenceContact];
      let bValue = b[field as keyof MarketIntelligenceContact];

      // Handle different data types
      if (field === 'confidence') {
        aValue = (aValue as number) || 0;
        bValue = (bValue as number) || 0;
      } else if (field === 'created_at' || field === 'updated_at') {
        aValue = new Date(aValue as string);
        bValue = new Date(bValue as string);
      } else {
        aValue = (aValue || '').toString().toLowerCase();
        bValue = (bValue || '').toString().toLowerCase();
      }

      // Sort order
      if (order === 'desc') {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      } else {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      }
    });

    return {
      ...store,
      filteredContacts: sortedContacts,
      sort: { field, order }
    };
  });
};

export const goToPage = (page: number) => {
  contactStore.update(store => ({
    ...store,
    currentPage: page
  }));
};

export const toggleContactSelection = (contactId: string) => {
  contactStore.update(store => {
    const selectedContacts = new Set(store.selectedContacts);
    
    if (selectedContacts.has(contactId)) {
      selectedContacts.delete(contactId);
    } else {
      selectedContacts.add(contactId);
    }

    return { ...store, selectedContacts };
  });
};

export const toggleSelectAll = () => {
  contactStore.update(store => {
    const startIndex = (store.currentPage - 1) * store.itemsPerPage;
    const endIndex = startIndex + store.itemsPerPage;
    const pageContacts = store.filteredContacts.slice(startIndex, endIndex);
    
    const allSelected = pageContacts.every(contact => 
      store.selectedContacts.has(contact.id.toString())
    );

    const selectedContacts = new Set(store.selectedContacts);

    if (allSelected) {
      // Deselect all
      pageContacts.forEach(contact => selectedContacts.delete(contact.id.toString()));
    } else {
      // Select all visible
      pageContacts.forEach(contact => selectedContacts.add(contact.id.toString()));
    }

    return { ...store, selectedContacts };
  });
};

export const clearAllFilters = () => {
  contactStore.update(store => ({
    ...store,
    filters: initialState.filters,
    filteredContacts: store.contacts,
    currentPage: 1,
    selectedContacts: new Set()
  }));
};

// Derived stores for computed values
export const paginatedContacts = derived(contactStore, ($store) => {
  const startIndex = ($store.currentPage - 1) * $store.itemsPerPage;
  const endIndex = startIndex + $store.itemsPerPage;
  return $store.filteredContacts.slice(startIndex, endIndex);
});

export const totalPages = derived(contactStore, ($store) => {
  return Math.ceil($store.filteredContacts.length / $store.itemsPerPage);
});

export const selectedCount = derived(contactStore, ($store) => {
  return $store.selectedContacts.size;
});

export const hasNextPage = derived([contactStore, totalPages], ([$store, $totalPages]) => {
  return $store.currentPage < $totalPages;
});

export const hasPrevPage = derived(contactStore, ($store) => {
  return $store.currentPage > 1;
});