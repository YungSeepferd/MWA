import { c as create_ssr_component, f as createEventDispatcher, d as add_attribute, a as escape, e as each } from "../../../../chunks/index3.js";
import "devalue";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: "button.selected.svelte-1n7jv6a{background-color:var(--primary-600);color:white;border-color:var(--primary-600)}button.active.svelte-1n7jv6a{background-color:var(--primary-600);color:white}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { data } = $$props;
  let formData = {
    name: "",
    min_price: 500,
    max_price: 2e3,
    min_rooms: 1,
    districts: [],
    move_in_date: "",
    amenities: [],
    providers: ["immoscout", "wg_gesucht"],
    schedule_type: "hourly",
    custom_interval: 60
  };
  let selectedDistricts = /* @__PURE__ */ new Set();
  createEventDispatcher();
  const munichDistricts = [
    {
      id: 1,
      name: "Altstadt-Lehel",
      code: "01"
    },
    {
      id: 2,
      name: "Ludwigsvorstadt-Isarvorstadt",
      code: "02"
    },
    { id: 3, name: "Maxvorstadt", code: "03" },
    {
      id: 4,
      name: "Schwabing-West",
      code: "04"
    },
    { id: 5, name: "Au-Haidhausen", code: "05" },
    {
      id: 6,
      name: "Schwabing-Freimann",
      code: "06"
    },
    {
      id: 7,
      name: "Neuhausen-Nymphenburg",
      code: "07"
    },
    { id: 8, name: "Moosach", code: "08" },
    {
      id: 9,
      name: "Milbertshofen-Am Hart",
      code: "09"
    },
    {
      id: 10,
      name: "Schwanthalerhöhe",
      code: "10"
    },
    { id: 11, name: "Laim", code: "11" },
    {
      id: 12,
      name: "Thalkirchen-Obersendling-Forstenried",
      code: "12"
    },
    { id: 13, name: "Hadern", code: "13" },
    {
      id: 14,
      name: "Pasing-Obermenzing",
      code: "14"
    },
    {
      id: 15,
      name: "Aubing-Lochhausen-Langwied",
      code: "15"
    },
    {
      id: 16,
      name: "Ramersdorf-Perlach",
      code: "16"
    },
    {
      id: 17,
      name: "Trudering-Riem",
      code: "17"
    },
    { id: 18, name: "Berg am Laim", code: "18" },
    { id: 19, name: "Bogenhausen", code: "19" },
    {
      id: 20,
      name: "Untergiesing-Harlaching",
      code: "20"
    },
    {
      id: 21,
      name: "Thalkirchen-Obersendling-Forstenried-Fürstenried",
      code: "21"
    },
    { id: 22, name: "Laim", code: "22" },
    { id: 23, name: "Lohhof", code: "23" },
    { id: 24, name: "Taufkirchen", code: "24" },
    { id: 25, name: "Unterhaching", code: "25" }
  ];
  const groupedAmenities = data.amenities.reduce(
    (groups, amenity) => {
      const category = amenity.category || "other";
      if (!groups[category])
        groups[category] = [];
      groups[category].push(amenity);
      return groups;
    },
    {}
  );
  if ($$props.data === void 0 && $$bindings.data && data !== void 0)
    $$bindings.data(data);
  $$result.css.add(css);
  return `<div class="search-creation"><div class="container mx-auto px-4 py-6 max-w-6xl">
    <div class="mb-8"><h1 class="text-3xl font-bold text-gray-900 mb-2">Create New Search</h1>
      <p class="text-gray-600">Configure your apartment search criteria and schedule</p></div>

    
    <div class="flex justify-center mb-6"><div class="bg-gray-100 rounded-lg p-1 flex"><button class="${[
    "px-4 py-2 rounded-md transition-colors svelte-1n7jv6a",
    "active"
  ].join(" ").trim()}">Visual Editor
        </button>
        <button class="${[
    "px-4 py-2 rounded-md transition-colors svelte-1n7jv6a",
    ""
  ].join(" ").trim()}">Advanced
        </button></div></div>

    <form method="POST" action="?/create" class="space-y-8">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><h2 class="text-xl font-semibold text-gray-900 mb-4">Basic Information</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6"><div><label for="search-name" class="block text-sm font-medium text-gray-700 mb-2">Search Name
            </label>
            <input id="search-name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500" placeholder="My Apartment Search" required${add_attribute("value", formData.name, 0)}></div></div></div>

      
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><h2 class="text-xl font-semibold text-gray-900 mb-4">Price Range</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6"><div><label for="min-price" class="block text-sm font-medium text-gray-700 mb-2">Minimum Price (€)
            </label>
            <input id="min-price" type="number" min="0" max="10000" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"${add_attribute("value", formData.min_price, 0)}></div>
          
          <div><label for="max-price" class="block text-sm font-medium text-gray-700 mb-2">Maximum Price (€)
            </label>
            <input id="max-price" type="number" min="0" max="10000" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"${add_attribute("value", formData.max_price, 0)}></div></div>
        
        <div class="mt-4"><div class="text-sm text-gray-600">Price Range: €${escape(formData.min_price)} - €${escape(formData.max_price)}</div></div></div>

      
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><h2 class="text-xl font-semibold text-gray-900 mb-4">Rooms</h2>
        
        <div class="flex flex-wrap gap-4">${each([1, 2, 3, 4, 5], (rooms) => {
    return `<label class="flex items-center"><input type="radio" name="rooms"${add_attribute("value", rooms, 0)} class="mr-2"${rooms === formData.min_rooms ? add_attribute("checked", true, 1) : ""}>
              <span class="text-sm text-gray-700">${escape(rooms)}+ rooms</span>
            </label>`;
  })}</div></div>

      
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><h2 class="text-xl font-semibold text-gray-900 mb-4">Munich Districts</h2>
        <p class="text-sm text-gray-600 mb-4">Select the districts you want to search in</p>
        
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">${each(munichDistricts, (district) => {
    return `<button type="button" class="${[
      "p-3 border border-gray-300 rounded-lg text-center hover:bg-gray-50 transition-colors svelte-1n7jv6a",
      selectedDistricts.has(district.id) ? "selected" : ""
    ].join(" ").trim()}"><div class="text-sm font-medium text-gray-900">${escape(district.code)}</div>
              <div class="text-xs text-gray-600 truncate">${escape(district.name)}</div>
            </button>`;
  })}</div>
        
        <div class="mt-4 text-sm text-gray-600">Selected: ${escape(selectedDistricts.size)} districts
        </div></div>

      
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><h2 class="text-xl font-semibold text-gray-900 mb-4">Move-in Date</h2>
        
        <input type="date" class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"${add_attribute("value", formData.move_in_date, 0)}></div>

      
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><h2 class="text-xl font-semibold text-gray-900 mb-4">Providers</h2>
        <p class="text-sm text-gray-600 mb-4">Select the platforms to search on</p>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">${each(data.providers, (provider) => {
    return `<label class="flex items-center p-3 border border-gray-300 rounded-lg hover:bg-gray-50 cursor-pointer"><input type="checkbox" ${formData.providers.includes(provider.id) ? "checked" : ""} class="mr-3">
              <span class="text-sm font-medium text-gray-700">${escape(provider.name)}</span>
              ${!provider.enabled ? `<span class="ml-2 px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">Coming Soon</span>` : ``}
            </label>`;
  })}</div></div>

      
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><h2 class="text-xl font-semibold text-gray-900 mb-4">Amenities</h2>
        
        ${each(Object.entries(groupedAmenities), ([category, amenities]) => {
    return `<div class="mb-6"><h3 class="text-lg font-medium text-gray-900 mb-3 capitalize">${escape(category)}</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">${each(amenities, (amenity) => {
      return `<label class="flex items-center"><input type="checkbox" ${formData.amenities.includes(amenity.id) ? "checked" : ""} class="mr-2">
                  <span class="text-sm text-gray-700">${escape(amenity.name)}</span>
                </label>`;
    })}</div>
          </div>`;
  })}</div>

      
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><h2 class="text-xl font-semibold text-gray-900 mb-4">Schedule</h2>
        
        <div class="space-y-4"><div class="flex flex-wrap gap-4"><label class="flex items-center"><input type="radio" name="schedule" value="hourly" class="mr-2"${add_attribute("checked", true, 1)}>
              <span class="text-sm text-gray-700">Hourly</span></label>
            <label class="flex items-center"><input type="radio" name="schedule" value="daily" class="mr-2"${""}>
              <span class="text-sm text-gray-700">Daily</span></label>
            <label class="flex items-center"><input type="radio" name="schedule" value="custom" class="mr-2"${""}>
              <span class="text-sm text-gray-700">Custom</span></label></div>
          
          ${``}</div></div>

      
      <div class="flex justify-end space-x-4 pt-6"><button type="button" class="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel
        </button>
        <button type="button" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors" ${""}>${escape("Preview Search")}</button>
        <button type="button" class="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors" ${""}>${escape("Save Search")}</button>
        <button type="button" class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors" ${""}>${escape("Start Search")}</button></div></form></div>
</div>`;
});
export {
  Page as default
};
