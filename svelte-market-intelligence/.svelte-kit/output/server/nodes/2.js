import * as universal from '../entries/pages/_page.js';

export const index = 2;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/+page.js";
export const imports = ["_app/immutable/nodes/2.338fb4c0.js","_app/immutable/chunks/index.8f2ca6db.js","_app/immutable/chunks/control.c2cf8273.js","_app/immutable/chunks/index.3da97a40.js","_app/immutable/chunks/navigation.e2e23cce.js","_app/immutable/chunks/singletons.71d606f7.js","_app/immutable/chunks/index.25c19884.js","_app/immutable/chunks/MobileNav.343364e7.js","_app/immutable/chunks/LineChart.7186ab17.js","_app/immutable/chunks/websocket.66ffcde3.js","_app/immutable/chunks/api.f5325af4.js","_app/immutable/chunks/errorHandler.253b2d9d.js"];
export const stylesheets = ["_app/immutable/assets/2.4c34445f.css","_app/immutable/assets/MobileNav.021b174d.css","_app/immutable/assets/LineChart.7b0ebd2a.css"];
export const fonts = [];
