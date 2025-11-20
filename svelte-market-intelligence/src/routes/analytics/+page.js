import { error } from '@sveltejs/kit';

/** @type {import('./$types').PageLoad} */
export async function load({ fetch }) {
  try {
    // Fetch analytics data
    const analyticsResponse = await fetch('/api/v1/analytics');
    
    if (!analyticsResponse.ok) {
      throw new Error(`API Error: ${analyticsResponse.status} ${analyticsResponse.statusText}`);
    }
    
    const analytics = await analyticsResponse.json();
    
    // Fetch contact statistics
    const statsResponse = await fetch('/api/v1/contacts/statistics/summary');
    let stats = null;
    
    if (statsResponse.ok) {
      stats = await statsResponse.json();
    }
    
    return {
      analytics,
      stats
    };
  } catch (err) {
    console.error('Error loading analytics:', err);
    error(500, 'Failed to load analytics data');
  }
}