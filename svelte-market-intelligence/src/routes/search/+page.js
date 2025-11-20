import { error } from '@sveltejs/kit';

export async function load({ fetch }) {
  try {
    // Load search configurations and statistics
    const [configurationsResponse, statisticsResponse] = await Promise.all([
      fetch('/api/v1/search/configurations').catch(() => ({ ok: false })),
      fetch('/api/v1/search/statistics').catch(() => ({ ok: false }))
    ]);

    const configurations = configurationsResponse.ok ? await configurationsResponse.json() : [];
    const statistics = statisticsResponse.ok ? await statisticsResponse.json() : {
      total_searches: 0,
      running_searches: 0,
      results_today: 0,
      success_rate: 0
    };

    return {
      configurations,
      statistics
    };
  } catch (err) {
    console.error('Error loading search data:', err);
    return {
      configurations: [],
      statistics: {
        total_searches: 0,
        running_searches: 0,
        results_today: 0,
        success_rate: 0
      }
    };
  }
}