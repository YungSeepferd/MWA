import { c as create_ssr_component, d as add_attribute, e as each, v as validate_component } from "../../../chunks/index3.js";
/* empty css                                                          */import { M as MobileNav } from "../../../chunks/MobileNav.js";
/* empty css                                                       */const css$1 = {
  code: ".animate-pulse.svelte-12p0sae{animation:svelte-12p0sae-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite}@keyframes svelte-12p0sae-pulse{0%,100%{opacity:1}50%{opacity:0.5}}.loading-skeleton-card.svelte-12p0sae{min-height:80px}.loading-skeleton-text.svelte-12p0sae{min-height:20px}.loading-skeleton-circle.svelte-12p0sae{min-height:40px;min-width:40px}.loading-skeleton-line.svelte-12p0sae{min-height:16px}",
  map: null
};
const LoadingSkeleton = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { type = "card" } = $$props;
  let { height = "auto" } = $$props;
  let { width = "100%" } = $$props;
  let { count = 1 } = $$props;
  if ($$props.type === void 0 && $$bindings.type && type !== void 0)
    $$bindings.type(type);
  if ($$props.height === void 0 && $$bindings.height && height !== void 0)
    $$bindings.height(height);
  if ($$props.width === void 0 && $$bindings.width && width !== void 0)
    $$bindings.width(width);
  if ($$props.count === void 0 && $$bindings.count && count !== void 0)
    $$bindings.count(count);
  $$result.css.add(css$1);
  return `${type === "card" ? `<div class="loading-skeleton-card bg-gray-200 rounded-lg animate-pulse svelte-12p0sae"${add_attribute("style", `height: ${height}; width: ${width};`, 0)}><div class="p-4"><div class="h-4 bg-gray-300 rounded mb-3 w-3/4"></div>
      <div class="h-3 bg-gray-300 rounded mb-2 w-1/2"></div>
      <div class="h-3 bg-gray-300 rounded w-2/3"></div></div></div>` : `${type === "text" ? `<div class="loading-skeleton-text space-y-2 svelte-12p0sae"${add_attribute("style", `width: ${width};`, 0)}>${each(Array(count), (_, i) => {
    return `<div class="h-4 bg-gray-200 rounded animate-pulse svelte-12p0sae"${add_attribute("style", `width: ${i % 2 === 0 ? "100%" : "80%"};`, 0)}></div>`;
  })}</div>` : `${type === "circle" ? `<div class="loading-skeleton-circle bg-gray-200 rounded-full animate-pulse svelte-12p0sae"${add_attribute("style", `height: ${height}; width: ${width};`, 0)}></div>` : `${type === "line" ? `<div class="loading-skeleton-line bg-gray-200 rounded animate-pulse svelte-12p0sae"${add_attribute("style", `height: ${height}; width: ${width};`, 0)}></div>` : ``}`}`}`}`;
});
const PieChart_svelte_svelte_type_style_lang = "";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".bg-gray-50.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{background:var(--gray-50)}.bg-primary-50.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{background:var(--primary-50)}.bg-success-50.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{background:color-mix(in srgb, var(--success-500) 10%, transparent)}.bg-warning-50.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{background:color-mix(in srgb, var(--warning-500) 10%, transparent)}.text-gray-900.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{color:var(--gray-900)}.text-gray-600.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{color:var(--gray-600)}.text-gray-500.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{color:var(--gray-500)}.text-gray-700.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{color:var(--gray-700)}.text-primary-600.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{color:var(--primary-600)}.text-success-600.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{color:var(--success-600)}.text-warning-600.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{color:var(--warning-600)}.text-error-600.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{color:var(--error-600)}.text-2xl.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{font-size:var(--font-size-2xl)}.text-xl.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{font-size:var(--font-size-xl)}.text-sm.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{font-size:var(--font-size-sm)}.text-3xl.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{font-size:var(--font-size-3xl)}.text-4xl.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{font-size:2.25rem}.font-bold.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{font-weight:600}.font-semibold.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{font-weight:500}.font-medium.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{font-weight:500}.mb-1.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{margin-bottom:var(--space-1)}.mb-2.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{margin-bottom:var(--space-2)}.mb-4.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{margin-bottom:var(--space-4)}.mb-6.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{margin-bottom:var(--space-6)}.py-6.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{padding-top:var(--space-6);padding-bottom:var(--space-6)}.py-8.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{padding-top:var(--space-8);padding-bottom:var(--space-8)}.px-4.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{padding-left:var(--space-4);padding-right:var(--space-4)}.p-3.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{padding:var(--space-3)}.p-4.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{padding:var(--space-4)}.p-8.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{padding:var(--space-8)}.pb-20.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{padding-bottom:5rem}.rounded-lg.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{border-radius:var(--radius-lg)}.space-y-3.svelte-1ajmma2>.svelte-1ajmma2+.svelte-1ajmma2{margin-top:var(--space-3)}.gap-3.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{gap:var(--space-3)}.gap-4.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{gap:var(--space-4)}.gap-6.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{gap:var(--space-6)}.flex.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{display:flex}.items-center.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{align-items:center}.justify-between.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{justify-content:space-between}.justify-center.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{justify-content:center}.w-full.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{width:100%}.text-center.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{text-align:center}.text-left.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{text-align:left}.text-right.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{text-align:right}.min-h-screen.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{min-height:100vh}.container.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{width:100%;margin:0 auto;padding:0 var(--space-4)}.mx-auto.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{margin-left:auto;margin-right:auto}.grid.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{display:grid}.border-b.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{border-bottom-width:1px}.border-gray-200.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{border-color:var(--gray-200)}.border-gray-100.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{border-color:var(--gray-100)}.overflow-x-auto.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{overflow-x:auto}table.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{border-collapse:collapse}th.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2,td.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{padding:var(--space-3)}.capitalize.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{text-transform:capitalize}@media(min-width: 768px){.md\\:grid-cols-2.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{grid-template-columns:repeat(2, 1fr)}}@media(min-width: 1024px){.lg\\:grid-cols-3.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{grid-template-columns:repeat(3, 1fr)}.lg\\:grid-cols-4.svelte-1ajmma2.svelte-1ajmma2.svelte-1ajmma2{grid-template-columns:repeat(4, 1fr)}}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { data } = $$props;
  let currentTimeframe = "30";
  if ($$props.data === void 0 && $$bindings.data && data !== void 0)
    $$bindings.data(data);
  $$result.css.add(css);
  data?.analytics?.agency_type_distribution || {};
  data?.analytics?.total_contacts || 0;
  data?.analytics?.monthly_trends?.map((trend) => ({
    month: trend.month,
    value: trend.contacts_added
  })) || [];
  data?.analytics?.monthly_trends?.map((trend) => ({
    month: trend.month,
    value: Math.round(trend.average_score * 100)
  })) || [];
  return `<div class="min-h-screen bg-gray-50 pb-20 svelte-1ajmma2"><div class="container mx-auto px-4 py-6 svelte-1ajmma2">
    <header class="mb-6 svelte-1ajmma2"><div class="flex justify-between items-start svelte-1ajmma2"><div><h1 class="text-2xl font-bold text-gray-900 mb-2 svelte-1ajmma2">Market Intelligence Analytics</h1>
          <p class="text-gray-600 svelte-1ajmma2">Comprehensive insights into your contact database and market trends</p></div>
        <div class="flex gap-3 svelte-1ajmma2">
          <div class="flex items-center gap-2 svelte-1ajmma2"><label class="text-sm font-medium text-gray-700 svelte-1ajmma2">Timeframe:</label>
            <select class="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white svelte-1ajmma2"${add_attribute("value", currentTimeframe, 0)}><option value="7">Last 7 days</option><option value="30">Last 30 days</option><option value="90">Last 90 days</option><option value="365">Last year</option><option value="all">All time</option></select></div>
          
          
          <button class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 svelte-1ajmma2">Export Data
          </button></div></div></header>

    ${`
      <div class="space-y-6">${validate_component(LoadingSkeleton, "LoadingSkeleton").$$render($$result, { type: "card", height: "120px" }, {}, {})}
        ${validate_component(LoadingSkeleton, "LoadingSkeleton").$$render($$result, { type: "card", height: "200px" }, {}, {})}
        ${validate_component(LoadingSkeleton, "LoadingSkeleton").$$render($$result, { type: "card", height: "250px" }, {}, {})}
        ${validate_component(LoadingSkeleton, "LoadingSkeleton").$$render($$result, { type: "card", height: "180px" }, {}, {})}</div>`}</div>

  
  ${validate_component(MobileNav, "MobileNav").$$render($$result, {}, {}, {})}
</div>`;
});
export {
  Page as default
};
