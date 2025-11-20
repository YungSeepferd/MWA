// @ts-nocheck
import { error } from '@sveltejs/kit';

/** @param {Parameters<import('./$types').PageLoad>[0]} event */
export async function load({ fetch, url }) {
  try {
    // Get query parameters for filtering
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('pageSize') || '20');
    const search = url.searchParams.get('search') || '';
    
    // Build API URL with query parameters
    const queryParams = new URLSearchParams();
    if (page) queryParams.append('page', page.toString());
    if (pageSize) queryParams.append('page_size', pageSize.toString());
    if (search) queryParams.append('search', search);
    
    const apiUrl = `/api/v1/contacts${queryParams.toString() ? `?${queryParams}` : ''}`;
    
    // Fetch contacts using SvelteKit's enhanced fetch
    const response = await fetch(apiUrl);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    
    return {
      contacts: data.contacts || [],
      pagination: {
        page,
        pageSize,
        totalItems: data.total || 0,
        totalPages: Math.ceil((data.total || 0) / pageSize)
      },
      filters: {
        page,
        pageSize,
        search
      }
    };
  } catch (err) {
    console.error('Error loading contacts:', err);
    error(500, 'Failed to load contacts');
  }
}