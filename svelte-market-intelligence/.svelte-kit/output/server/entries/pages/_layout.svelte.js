import { c as create_ssr_component, o as onDestroy, e as each, a as escape, n as null_to_empty, v as validate_component } from "../../chunks/index3.js";
import { w as wsService } from "../../chunks/api.js";
const app = "";
const RealTimeNotification_svelte_svelte_type_style_lang = "";
const css$1 = {
  code: ".notification-enter.svelte-125dlm3{opacity:0;transform:translateX(100%)}.notification-enter-active.svelte-125dlm3{opacity:1;transform:translateX(0);transition:opacity 300ms, transform 300ms}.notification-exit.svelte-125dlm3{opacity:1;transform:translateX(0)}.notification-exit-active.svelte-125dlm3{opacity:0;transform:translateX(100%);transition:opacity 300ms, transform 300ms}",
  map: null
};
const RealTimeNotification = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let notifications = [];
  let nextId = 1;
  onDestroy(() => {
    wsService.off("contact_created", handleContactCreated);
    wsService.off("contact_updated", handleContactUpdated);
    wsService.off("contact_deleted", handleContactDeleted);
    wsService.off("analytics_updated", handleAnalyticsUpdated);
    wsService.off("system_notification", handleSystemNotification);
    wsService.disconnect();
  });
  const handleContactCreated = (data) => {
    addNotification(`New contact created: ${data.name}`, "success");
  };
  const handleContactUpdated = (data) => {
    addNotification(`Contact updated: ${data.name}`, "info");
  };
  const handleContactDeleted = (data) => {
    addNotification(`Contact deleted: ${data.name}`, "warning");
  };
  const handleAnalyticsUpdated = (data) => {
    addNotification("Analytics data updated", "info");
  };
  const handleSystemNotification = (data) => {
    addNotification(data.message, data.type || "info");
  };
  const addNotification = (message, type = "info") => {
    const id = nextId++;
    notifications.push({
      id,
      message,
      type,
      timestamp: /* @__PURE__ */ new Date()
    });
    setTimeout(
      () => {
        removeNotification(id);
      },
      5e3
    );
  };
  const removeNotification = (id) => {
    notifications = notifications.filter((n) => n.id !== id);
  };
  const getNotificationColor = (type) => {
    switch (type) {
      case "success":
        return "bg-green-50 border-green-200 text-green-800";
      case "error":
        return "bg-red-50 border-red-200 text-red-800";
      case "warning":
        return "bg-yellow-50 border-yellow-200 text-yellow-800";
      case "info":
        return "bg-blue-50 border-blue-200 text-blue-800";
      default:
        return "bg-gray-50 border-gray-200 text-gray-800";
    }
  };
  const getNotificationIcon = (type) => {
    switch (type) {
      case "success":
        return "✓";
      case "error":
        return "✗";
      case "warning":
        return "⚠";
      case "info":
        return "ℹ";
      default:
        return "•";
    }
  };
  $$result.css.add(css$1);
  return `<div class="fixed top-4 right-4 z-50 space-y-2 max-w-sm">${each(notifications, (notification) => {
    return `<div class="${escape(null_to_empty(`p-3 rounded-lg border shadow-sm transition-all duration-300 ${getNotificationColor(notification.type)}`), true) + " svelte-125dlm3"}" role="alert"><div class="flex items-center justify-between"><div class="flex items-center space-x-2"><span class="text-sm font-medium">${escape(getNotificationIcon(notification.type))}</span>
          <span class="text-sm">${escape(notification.message)}</span></div>
        <button class="text-gray-500 hover:text-gray-700 text-sm" aria-label="Dismiss notification">×
        </button></div>
      <div class="text-xs text-gray-600 mt-1">${escape(notification.timestamp.toLocaleTimeString("de-DE"))}</div>
    </div>`;
  })}

  
  <div class="${escape(
    null_to_empty(`p-2 rounded-lg border text-xs ${"bg-yellow-50 border-yellow-200 text-yellow-800"}`),
    true
  ) + " svelte-125dlm3"}">${escape("🟡 Connecting...")}</div>
</div>`;
});
const ErrorBoundary_svelte_svelte_type_style_lang = "";
const css = {
  code: ".error-boundary.svelte-gvwm50{max-width:600px;margin:0 auto}",
  map: null
};
const ErrorBoundary = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  $$result.css.add(css);
  return `${`${slots.default ? slots.default({}) : ``}`}`;
});
const Layout = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  return `${$$result.head += `<!-- HEAD_svelte-129uzdq_START -->${$$result.title = `<title>MWA Market Intelligence</title>`, ""}<meta name="viewport" content="width=device-width, initial-scale=1.0"><meta name="description" content="Market Intelligence Dashboard for MWA - Real-time contact management and analytics"><!-- HEAD_svelte-129uzdq_END -->`, ""}

${validate_component(ErrorBoundary, "ErrorBoundary").$$render($$result, {}, {}, {
    default: () => {
      return `${validate_component(RealTimeNotification, "RealTimeNotification").$$render($$result, {}, {}, {})}
  ${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
export {
  Layout as default
};
