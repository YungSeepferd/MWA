import { c as create_ssr_component, a as escape, n as null_to_empty, o as onDestroy, v as validate_component } from "../../chunks/index3.js";
import { M as MobileNav } from "../../chunks/MobileNav.js";
/* empty css                                                    */import "../../chunks/websocket.js";
const LoadingSkeleton_svelte_svelte_type_style_lang = "";
const css$1 = {
  code: ".skeleton.svelte-1kqgc11{background:linear-gradient(90deg, var(--gray-200) 25%, var(--gray-300) 50%, var(--gray-200) 75%);background-size:200% 100%;animation:svelte-1kqgc11-loading 1.5s infinite}.rounded.svelte-1kqgc11{border-radius:var(--radius-md)}.rounded-full.svelte-1kqgc11{border-radius:50%}.h-full.svelte-1kqgc11{height:100%}.h-4.svelte-1kqgc11{height:1rem}.h-10.svelte-1kqgc11{height:2.5rem}.aspect-square.svelte-1kqgc11{aspect-ratio:1 / 1}@keyframes svelte-1kqgc11-loading{0%{background-position:200% 0}100%{background-position:-200% 0}}",
  map: null
};
const LoadingSkeleton = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { type = "card" } = $$props;
  let { height = "auto" } = $$props;
  let { width = "100%" } = $$props;
  let { className = "" } = $$props;
  const getSkeletonClass = () => {
    const baseClass = "skeleton rounded";
    switch (type) {
      case "card":
        return `${baseClass} h-full`;
      case "text":
        return `${baseClass} h-4`;
      case "circle":
        return `${baseClass} rounded-full aspect-square`;
      case "button":
        return `${baseClass} h-10`;
      default:
        return baseClass;
    }
  };
  if ($$props.type === void 0 && $$bindings.type && type !== void 0)
    $$bindings.type(type);
  if ($$props.height === void 0 && $$bindings.height && height !== void 0)
    $$bindings.height(height);
  if ($$props.width === void 0 && $$bindings.width && width !== void 0)
    $$bindings.width(width);
  if ($$props.className === void 0 && $$bindings.className && className !== void 0)
    $$bindings.className(className);
  $$result.css.add(css$1);
  return `<div class="${escape(null_to_empty(`${getSkeletonClass()} ${className}`), true) + " svelte-1kqgc11"}" style="${"height: " + escape(height, true) + "; width: " + escape(width, true) + ";"}"></div>`;
});
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".bg-gray-50.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{background:var(--gray-50)}.bg-primary-100.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{background:var(--primary-100)}.bg-success-100.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{background:var(--success-100)}.bg-warning-100.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{background:var(--warning-100)}.bg-gray-100.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{background:var(--gray-100)}.text-gray-900.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{color:var(--gray-900)}.text-gray-600.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{color:var(--gray-600)}.text-gray-500.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{color:var(--gray-500)}.text-gray-700.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{color:var(--gray-700)}.text-primary-600.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{color:var(--primary-600)}.text-success-600.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{color:var(--success-600)}.text-warning-600.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{color:var(--warning-600)}.text-error-600.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{color:var(--error-600)}.text-info-600.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{color:var(--info-600)}.text-3xl.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{font-size:var(--font-size-3xl)}.text-2xl.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{font-size:var(--font-size-2xl)}.text-xl.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{font-size:var(--font-size-xl)}.text-sm.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{font-size:var(--font-size-sm)}.text-xs.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{font-size:var(--font-size-xs)}.font-bold.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{font-weight:600}.font-semibold.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{font-weight:500}.font-medium.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{font-weight:500}.mb-1.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{margin-bottom:var(--space-1)}.mb-2.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{margin-bottom:var(--space-2)}.mb-4.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{margin-bottom:var(--space-4)}.mb-6.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{margin-bottom:var(--space-6)}.py-6.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{padding-top:var(--space-6);padding-bottom:var(--space-6)}.py-4.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{padding-top:var(--space-4);padding-bottom:var(--space-4)}.py-8.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{padding-top:var(--space-8);padding-bottom:var(--space-8)}.px-4.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{padding-left:var(--space-4);padding-right:var(--space-4)}.p-2.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{padding:var(--space-2)}.p-3.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{padding:var(--space-3)}.p-4.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{padding:var(--space-4)}.pb-20.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{padding-bottom:5rem}.rounded-lg.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{border-radius:var(--radius-lg)}.rounded.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{border-radius:var(--radius)}.rounded-full.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{border-radius:9999px}.space-y-3.svelte-wbu9mj>.svelte-wbu9mj+.svelte-wbu9mj{margin-top:var(--space-3)}.space-y-6.svelte-wbu9mj>.svelte-wbu9mj+.svelte-wbu9mj{margin-top:var(--space-6)}.gap-3.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{gap:var(--space-3)}.gap-4.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{gap:var(--space-4)}.gap-6.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{gap:var(--space-6)}.flex.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{display:flex}.items-center.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{align-items:center}.justify-between.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{justify-content:space-between}.justify-center.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{justify-content:center}.w-full.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{width:100%}.w-8.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{width:2rem}.h-8.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{height:2rem}.text-center.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{text-align:center}.text-left.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{text-align:left}.min-h-screen.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{min-height:100vh}.container.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{width:100%;margin:0 auto;padding:0 var(--space-4)}.mx-auto.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{margin-left:auto;margin-right:auto}.grid.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{display:grid}.grid-cols-2.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{grid-template-columns:repeat(2, 1fr)}.grid-cols-4.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{grid-template-columns:repeat(4, 1fr)}.lg\\:grid-cols-3.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{grid-template-columns:repeat(3, 1fr)}.lg\\:col-span-2.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{grid-column:span 2}.status-indicator.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{display:flex;align-items:center;gap:0.5rem;padding:0.25rem 0.5rem;border-radius:0.25rem;font-size:0.75rem;font-weight:500}.status-indicator.connected.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{background:#dcfce7;color:#166534}.status-indicator.disconnected.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{background:#fef2f2;color:#dc2626}.status-dot.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{width:0.5rem;height:0.5rem;border-radius:50%;animation:svelte-wbu9mj-pulse 2s infinite}.status-indicator.connected.svelte-wbu9mj .status-dot.svelte-wbu9mj.svelte-wbu9mj{background:#16a34a}.status-indicator.disconnected.svelte-wbu9mj .status-dot.svelte-wbu9mj.svelte-wbu9mj{background:#dc2626}@keyframes svelte-wbu9mj-pulse{0%{opacity:1}50%{opacity:0.5}100%{opacity:1}}@media(min-width: 768px){.md\\:grid-cols-2.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{grid-template-columns:repeat(2, 1fr)}}@media(min-width: 1024px){.lg\\:grid-cols-3.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{grid-template-columns:repeat(3, 1fr)}.lg\\:grid-cols-4.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{grid-template-columns:repeat(4, 1fr)}.lg\\:col-span-2.svelte-wbu9mj.svelte-wbu9mj.svelte-wbu9mj{grid-column:span 2}}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { data } = $$props;
  let lastUpdated = /* @__PURE__ */ new Date();
  onDestroy(() => {
  });
  if ($$props.data === void 0 && $$bindings.data && data !== void 0)
    $$bindings.data(data);
  $$result.css.add(css);
  return `<div class="min-h-screen bg-gray-50 pb-20 svelte-wbu9mj"><div class="container mx-auto px-4 py-6 svelte-wbu9mj">
    <header class="mb-6 svelte-wbu9mj"><div class="flex items-center justify-between mb-2 svelte-wbu9mj"><div><h1 class="text-2xl font-bold text-gray-900 svelte-wbu9mj">Dashboard</h1>
          <p class="text-gray-600 svelte-wbu9mj">Welcome back! Here&#39;s your apartment search overview.</p></div>
        <div class="flex items-center gap-3 svelte-wbu9mj"><div class="${escape(null_to_empty(`status-indicator ${"disconnected"}`), true) + " svelte-wbu9mj"}"><span class="status-dot svelte-wbu9mj"></span>
            <span class="text-xs svelte-wbu9mj">${escape("Offline")}</span></div>
          <button class="btn btn-secondary" ${"disabled"}>${escape("Refreshing...")}</button></div></div>
      <p class="text-sm text-gray-500 svelte-wbu9mj"><i class="fas fa-clock me-1"></i>
        Last updated: ${escape(lastUpdated.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" }))}</p></header>

    ${`
      <div class="space-y-6">${validate_component(LoadingSkeleton, "LoadingSkeleton").$$render($$result, { type: "card", height: "120px" }, {}, {})}
        ${validate_component(LoadingSkeleton, "LoadingSkeleton").$$render($$result, { type: "card", height: "200px" }, {}, {})}
        ${validate_component(LoadingSkeleton, "LoadingSkeleton").$$render($$result, { type: "card", height: "150px" }, {}, {})}
        ${validate_component(LoadingSkeleton, "LoadingSkeleton").$$render($$result, { type: "card", height: "180px" }, {}, {})}</div>`}</div>

  
  ${validate_component(MobileNav, "MobileNav").$$render($$result, {}, {}, {})}
</div>`;
});
export {
  Page as default
};
