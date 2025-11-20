import { error } from '@sveltejs/kit';

/** @type {import('./$types').PageLoad} */
export async function load({ fetch }) {
  try {
    // Fetch all dashboard-related data
    const [analyticsResponse, statsResponse, activityResponse, sourcesResponse, statusResponse] = await Promise.all([
      fetch('/api/v1/analytics'),
      fetch('/api/v1/contacts/statistics/summary'),
      fetch('/api/v1/dashboard/activity?limit=10'),
      fetch('/api/v1/dashboard/sources?limit=5'),
      fetch('/api/v1/system/status')
    ]);

    // Handle responses with fallbacks
    const analytics = analyticsResponse.ok ? await analyticsResponse.json() : {
      total_contacts: 0,
      approved_contacts: 0,
      average_confidence_score: 0,
      outreach_success_rate: 0
    };

    const stats = statsResponse.ok ? await statsResponse.json() : {
      active_searches: 0,
      new_contacts_today: 0,
      pending_review: 0,
      success_rate: 0
    };

    const activity = activityResponse.ok ? await activityResponse.json() : [];
    const sources = sourcesResponse.ok ? await sourcesResponse.json() : [];
    const systemStatus = statusResponse.ok ? await statusResponse.json() : {
      scraper: { status: 'Unknown', state: 'unknown' },
      discovery: { status: 'Unknown', state: 'unknown' },
      notification: { status: 'Unknown', state: 'unknown' },
      database: { status: 'Unknown', state: 'unknown' }
    };

    return {
      analytics,
      stats,
      activity,
      sources,
      systemStatus,
      recentActivity: [] // Will be populated from WebSocket
    };
  } catch (err) {
    console.error('Error loading dashboard data:', err);
    // Return comprehensive fallback data for better UX
    return {
      analytics: {
        total_contacts: 0,
        approved_contacts: 0,
        average_confidence_score: 0,
        outreach_success_rate: 0
      },
      stats: {
        active_searches: 0,
        new_contacts_today: 0,
        pending_review: 0,
        success_rate: 0
      },
      activity: [],
      sources: [],
      systemStatus: {
        scraper: { status: 'Unknown', state: 'unknown' },
        discovery: { status: 'Unknown', state: 'unknown' },
        notification: { status: 'Unknown', state: 'unknown' },
        database: { status: 'Unknown', state: 'unknown' }
      },
      recentActivity: []
    };
  }
}