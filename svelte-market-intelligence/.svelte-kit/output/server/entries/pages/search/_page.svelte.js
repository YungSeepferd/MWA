import { c as create_ssr_component, f as createEventDispatcher, a as escape, e as each, d as add_attribute } from "../../../chunks/index3.js";
import "../../../chunks/websocket.js";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".search-management.svelte-6u4sl2{min-height:calc(100vh - 200px)}.badge.svelte-6u4sl2{padding:0.25rem 0.5rem;border-radius:0.375rem;font-size:0.75rem;font-weight:500}.badge-success.svelte-6u4sl2{background-color:var(--green-100);color:var(--green-800)}.badge-warning.svelte-6u4sl2{background-color:var(--yellow-100);color:var(--yellow-800)}.badge-info.svelte-6u4sl2{background-color:var(--blue-100);color:var(--blue-800)}.badge-error.svelte-6u4sl2{background-color:var(--red-100);color:var(--red-800)}.badge-secondary.svelte-6u4sl2{background-color:var(--gray-100);color:var(--gray-800)}button.active.svelte-6u4sl2{background-color:var(--primary-600);color:white}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { data } = $$props;
  let configurations = data.configurations || [];
  data.statistics || {};
  let searchStats = {
    total_searches: 0,
    running_searches: 0,
    results_today: 0,
    success_rate: 0
  };
  createEventDispatcher();
  const formatNumber = (num) => {
    return new Intl.NumberFormat("de-DE").format(num);
  };
  const getStatusBadgeColor = (status) => {
    const colors = {
      "running": "success",
      "paused": "warning",
      "completed": "info",
      "error": "error",
      "idle": "secondary"
    };
    return colors[status] || "secondary";
  };
  const formatRelativeTime = (timestamp) => {
    if (!timestamp)
      return "Never";
    const now = /* @__PURE__ */ new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / 6e4);
    if (diffMins < 1)
      return "Just now";
    if (diffMins < 60)
      return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24)
      return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };
  if ($$props.data === void 0 && $$bindings.data && data !== void 0)
    $$bindings.data(data);
  $$result.css.add(css);
  return `<div class="search-management svelte-6u4sl2"><div class="container mx-auto px-4 py-6">
    <div class="mb-8"><h1 class="text-3xl font-bold text-gray-900 mb-2">Search Management</h1>
      <p class="text-gray-600">Manage your apartment search configurations and monitor search performance</p></div>

    
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8"><div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><div class="flex items-center"><div class="p-3 rounded-full bg-blue-100 text-blue-600"><span class="text-xl">🔍</span></div>
          <div class="ml-4"><p class="text-sm font-medium text-gray-600">Total Searches</p>
            <p class="text-2xl font-bold text-gray-900">${escape(formatNumber(searchStats.total_searches))}</p></div></div></div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><div class="flex items-center"><div class="p-3 rounded-full bg-green-100 text-green-600"><span class="text-xl">▶️</span></div>
          <div class="ml-4"><p class="text-sm font-medium text-gray-600">Running</p>
            <p class="text-2xl font-bold text-gray-900">${escape(formatNumber(searchStats.running_searches))}</p></div></div></div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><div class="flex items-center"><div class="p-3 rounded-full bg-purple-100 text-purple-600"><span class="text-xl">📈</span></div>
          <div class="ml-4"><p class="text-sm font-medium text-gray-600">Results Today</p>
            <p class="text-2xl font-bold text-gray-900">${escape(formatNumber(searchStats.results_today))}</p></div></div></div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"><div class="flex items-center"><div class="p-3 rounded-full bg-yellow-100 text-yellow-600"><span class="text-xl">🎯</span></div>
          <div class="ml-4"><p class="text-sm font-medium text-gray-600">Success Rate</p>
            <p class="text-2xl font-bold text-gray-900">${escape(searchStats.success_rate)}%</p></div></div></div></div>

    
    <div class="flex justify-between items-center mb-6"><div class="flex space-x-4"><button class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">+ New Search
        </button>
        <button class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Import Search
        </button></div>
      
      <div class="flex space-x-2"><button class="${[
    "px-4 py-2 rounded-lg transition-colors svelte-6u4sl2",
    "active"
  ].join(" ").trim()}">Active (${escape(configurations.filter((c) => c.status === "running").length)})
        </button>
        <button class="${[
    "px-4 py-2 rounded-lg transition-colors svelte-6u4sl2",
    ""
  ].join(" ").trim()}">All (${escape(configurations.length)})
        </button></div></div>

    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">${configurations.filter((config) => config.status === "running").length ? each(configurations.filter((config) => config.status === "running"), (config) => {
    return `<div class="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"><div class="p-4 border-b border-gray-100"><div class="flex justify-between items-start"><h3 class="text-lg font-semibold text-gray-900">${escape(config.name)}</h3>
              <span class="${"badge badge-" + escape(getStatusBadgeColor(config.status), true) + " svelte-6u4sl2"}">${escape(config.status)}
              </span></div>
            
            <div class="mt-2 space-y-1 text-sm text-gray-600"><div class="flex justify-between"><span>Price:</span>
                <span>€${escape(formatNumber(config.min_price))} - €${escape(formatNumber(config.max_price))}</span></div>
              <div class="flex justify-between"><span>Rooms:</span>
                <span>${escape(config.min_rooms)}+</span></div>
              <div class="flex justify-between"><span>Districts:</span>
                <span>${escape(config.districts?.length || 0)}</span></div>
            </div></div>

          <div class="p-4 border-b border-gray-100"><div class="flex justify-between text-sm"><span>Last Run:</span>
              <span class="text-gray-600">${escape(formatRelativeTime(config.last_run))}</span></div>
            <div class="flex justify-between text-sm mt-1"><span>Results:</span>
              <span class="text-gray-600">${escape(config.results_count || 0)}</span>
            </div></div>

          <div class="p-3 flex justify-end space-x-2"><button class="p-2 text-gray-400 hover:text-blue-600 transition-colors" title="Edit Search"><span class="text-sm">✏️</span></button>
            <button class="p-2 text-gray-400 hover:text-green-600 transition-colors" ${""}${add_attribute(
      "title",
      config.status === "running" ? "Pause Search" : "Start Search",
      0
    )}><span class="text-sm">${escape(config.status === "running" ? "⏸️" : "▶️")}</span></button>
            <button class="p-2 text-gray-400 hover:text-red-600 transition-colors" title="Delete Search"><span class="text-sm">🗑️</span>
            </button></div>
        </div>`;
  }) : `<div class="col-span-full text-center py-12"><div class="text-6xl mb-4">🔍</div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">No Active Searches</h3>
          <p class="text-gray-600 mb-4">Create your first search to start finding apartments</p>
          <button class="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">Create Search
          </button>
        </div>`}</div></div>
</div>`;
});
export {
  Page as default
};
