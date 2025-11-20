async function load({ fetch }) {
  try {
    const [providersResponse, amenitiesResponse] = await Promise.all([
      fetch("/api/v1/search/providers").catch(() => ({ ok: false })),
      fetch("/api/v1/search/amenities").catch(() => ({ ok: false }))
    ]);
    const providers = providersResponse.ok ? await providersResponse.json() : [
      { id: "immoscout", name: "ImmobilienScout24", enabled: true },
      { id: "wg_gesucht", name: "WG-Gesucht", enabled: true },
      { id: "immowelt", name: "ImmoWelt", enabled: false }
    ];
    const amenities = amenitiesResponse.ok ? await amenitiesResponse.json() : [
      { id: "balcony", name: "Balcony", category: "outdoor" },
      { id: "garden", name: "Garden", category: "outdoor" },
      { id: "parking", name: "Parking", category: "parking" },
      { id: "garage", name: "Garage", category: "parking" },
      { id: "elevator", name: "Elevator", category: "building" },
      { id: "furnished", name: "Furnished", category: "interior" },
      { id: "kitchen", name: "Kitchen", category: "interior" },
      { id: "washing_machine", name: "Washing Machine", category: "appliances" }
    ];
    return {
      providers,
      amenities
    };
  } catch (err) {
    console.error("Error loading search form data:", err);
    return {
      providers: [],
      amenities: []
    };
  }
}
export {
  load
};
