import { c as create_ssr_component, e as each, d as add_attribute, a as escape } from "./index3.js";
const MobileNav_svelte_svelte_type_style_lang = "";
const css = {
  code: ".mobile-nav.svelte-1uhwhwy{position:fixed;bottom:0;left:0;right:0;background:white;border-top:1px solid var(--gray-200);padding:var(--space-2);z-index:1000;box-shadow:0 -2px 10px rgba(0, 0, 0, 0.1)}.flex.svelte-1uhwhwy{display:flex}.justify-between.svelte-1uhwhwy{justify-content:space-between}.items-center.svelte-1uhwhwy{align-items:center}.flex-col.svelte-1uhwhwy{flex-direction:column}.p-2.svelte-1uhwhwy{padding:var(--space-2)}.text-sm.svelte-1uhwhwy{font-size:var(--font-size-sm)}.text-lg.svelte-1uhwhwy{font-size:var(--font-size-lg)}.text-xs.svelte-1uhwhwy{font-size:var(--font-size-xs)}.text-gray-600.svelte-1uhwhwy{color:var(--gray-600)}.transition-colors.svelte-1uhwhwy{transition:color 0.2s ease}.mb-1.svelte-1uhwhwy{margin-bottom:var(--space-1)}a.svelte-1uhwhwy{-webkit-tap-highlight-color:transparent;border-radius:var(--radius-md);transition:background-color 0.2s ease}a.svelte-1uhwhwy:active{background-color:var(--gray-100)}",
  map: null
};
const MobileNav = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const menuItems = [
    {
      label: "Dashboard",
      icon: "🏠",
      href: "/"
    },
    {
      label: "Search",
      icon: "🔍",
      href: "/search"
    },
    {
      label: "Contacts",
      icon: "👥",
      href: "/contacts"
    },
    {
      label: "Analytics",
      icon: "📊",
      href: "/analytics"
    }
  ];
  $$result.css.add(css);
  return `<nav class="mobile-nav svelte-1uhwhwy"><div class="flex justify-between items-center svelte-1uhwhwy">${each(menuItems, (item) => {
    return `<a${add_attribute("href", item.href, 0)} class="flex flex-col items-center p-2 text-sm text-gray-600 hover:text-primary-600 transition-colors svelte-1uhwhwy"><span class="text-lg mb-1 svelte-1uhwhwy">${escape(item.icon)}</span>
        <span class="text-xs svelte-1uhwhwy">${escape(item.label)}</span>
      </a>`;
  })}</div>
</nav>`;
});
export {
  MobileNav as M
};
