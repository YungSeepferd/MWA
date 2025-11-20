import { c as create_ssr_component, a as escape, n as null_to_empty, v as validate_component } from "../../../chunks/index3.js";
const LoadingState_svelte_svelte_type_style_lang = "";
const css$1 = {
  code: ".loading-state.svelte-5ly2bv{min-height:100px}@keyframes svelte-5ly2bv-spin{to{transform:rotate(360deg)}}@keyframes svelte-5ly2bv-bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}@keyframes svelte-5ly2bv-pulse{0%,100%{opacity:1}50%{opacity:0.5}}.animate-spin.svelte-5ly2bv{animation:svelte-5ly2bv-spin 1s linear infinite}.animate-bounce.svelte-5ly2bv{animation:svelte-5ly2bv-bounce 1s infinite}.animate-pulse.svelte-5ly2bv{animation:svelte-5ly2bv-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite}",
  map: null
};
const LoadingState = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { type = "spinner" } = $$props;
  let { message = "Loading..." } = $$props;
  let { size = "medium" } = $$props;
  const sizeClasses = {
    small: "h-4 w-4",
    medium: "h-6 w-6",
    large: "h-8 w-8"
  };
  if ($$props.type === void 0 && $$bindings.type && type !== void 0)
    $$bindings.type(type);
  if ($$props.message === void 0 && $$bindings.message && message !== void 0)
    $$bindings.message(message);
  if ($$props.size === void 0 && $$bindings.size && size !== void 0)
    $$bindings.size(size);
  $$result.css.add(css$1);
  return `<div class="loading-state flex flex-col items-center justify-center p-4 svelte-5ly2bv">${type === "spinner" ? `<div class="${escape(null_to_empty(`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${sizeClasses[size]}`), true) + " svelte-5ly2bv"}"></div>` : `${type === "dots" ? `<div class="flex space-x-1"><div class="animate-bounce h-2 w-2 bg-gray-400 rounded-full svelte-5ly2bv"></div>
      <div class="animate-bounce h-2 w-2 bg-gray-400 rounded-full svelte-5ly2bv" style="animation-delay: 0.1s"></div>
      <div class="animate-bounce h-2 w-2 bg-gray-400 rounded-full svelte-5ly2bv" style="animation-delay: 0.2s"></div></div>` : `${type === "skeleton" ? `<div class="space-y-2"><div class="animate-pulse bg-gray-200 rounded h-4 w-32 svelte-5ly2bv"></div>
      <div class="animate-pulse bg-gray-200 rounded h-4 w-24 svelte-5ly2bv"></div></div>` : ``}`}`}
  
  ${message ? `<p class="text-sm text-gray-600 mt-2">${escape(message)}</p>` : ``}
</div>`;
});
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".test-page.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{min-height:100vh;background:var(--gray-50)}.card.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{background:white;border-radius:0.5rem;padding:1.5rem;box-shadow:0 1px 3px rgba(0, 0, 0, 0.1);border:1px solid #e5e7eb}.bg-success-50.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{background:color-mix(in srgb, var(--success-500) 10%, transparent)}.bg-error-50.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{background:color-mix(in srgb, var(--error-500) 10%, transparent)}.bg-warning-50.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{background:color-mix(in srgb, var(--warning-500) 10%, transparent)}.bg-primary-50.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{background:color-mix(in srgb, var(--primary-500) 10%, transparent)}.text-primary-600.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{color:var(--primary-600)}.text-success-600.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{color:var(--success-600)}.text-warning-600.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{color:var(--warning-600)}.text-3xl.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{font-size:var(--font-size-3xl)}.text-2xl.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{font-size:var(--font-size-2xl)}.text-xl.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{font-size:var(--font-size-xl)}.text-sm.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{font-size:var(--font-size-sm)}.font-bold.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{font-weight:600}.font-semibold.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{font-weight:500}.mb-2.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{margin-bottom:var(--space-2)}.mb-4.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{margin-bottom:var(--space-4)}.mb-8.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{margin-bottom:var(--space-8)}.py-6.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{padding-top:var(--space-6);padding-bottom:var(--space-6)}.px-4.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{padding-left:var(--space-4);padding-right:var(--space-4)}.space-y-6.svelte-5xav0c>.svelte-5xav0c+.svelte-5xav0c{margin-top:var(--space-6)}.gap-4.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{gap:var(--space-4)}.grid.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{display:grid}.grid-cols-2.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{grid-template-columns:repeat(2, 1fr)}.grid-cols-3.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{grid-template-columns:repeat(3, 1fr)}.text-center.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{text-align:center}.container.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{width:100%;margin:0 auto;padding:0 var(--space-4)}.mx-auto.svelte-5xav0c.svelte-5xav0c.svelte-5xav0c{margin-left:auto;margin-right:auto}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  $$result.css.add(css);
  return `<div class="test-page svelte-5xav0c"><div class="container mx-auto px-4 py-6 svelte-5xav0c"><header class="mb-8 svelte-5xav0c"><h1 class="text-3xl font-bold text-gray-900 mb-2 svelte-5xav0c">API Integration Test</h1>
      <p class="text-gray-600">Testing the Market Intelligence API integration with mock data</p></header>

    ${`<div class="flex justify-center py-12">${validate_component(LoadingState, "LoadingState").$$render(
    $$result,
    {
      type: "spinner",
      message: "Running API tests...",
      size: "large"
    },
    {},
    {}
  )}</div>`}</div>
</div>`;
});
export {
  Page as default
};
