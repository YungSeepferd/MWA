import { c as create_ssr_component, f as createEventDispatcher, a as escape, n as null_to_empty, d as add_attribute, e as each, b as subscribe, h as set_store_value, v as validate_component } from "../../../chunks/index3.js";
import { d as derived, w as writable } from "../../../chunks/index2.js";
const initialState = {
  contacts: [],
  filteredContacts: [],
  selectedContacts: /* @__PURE__ */ new Set(),
  currentPage: 1,
  itemsPerPage: 20,
  filters: {
    search: "",
    agencyType: "",
    confidence: "",
    status: ""
  },
  sort: {
    field: "created_at",
    order: "desc"
  },
  isLoading: false,
  error: null
};
const contactStore = writable(initialState);
const paginatedContacts = derived(contactStore, ($store) => {
  const startIndex = ($store.currentPage - 1) * $store.itemsPerPage;
  const endIndex = startIndex + $store.itemsPerPage;
  return $store.filteredContacts.slice(startIndex, endIndex);
});
const totalPages = derived(contactStore, ($store) => {
  return Math.ceil($store.filteredContacts.length / $store.itemsPerPage);
});
const selectedCount = derived(contactStore, ($store) => {
  return $store.selectedContacts.size;
});
const hasNextPage = derived([contactStore, totalPages], ([$store, $totalPages]) => {
  return $store.currentPage < $totalPages;
});
const hasPrevPage = derived(contactStore, ($store) => {
  return $store.currentPage > 1;
});
const ContactCard_svelte_svelte_type_style_lang = "";
const css = {
  code: ".contact-card.svelte-ktsfxp{min-height:200px}.contact-card.svelte-ktsfxp:hover{transform:translateY(-1px);transition:transform 0.2s ease-in-out}",
  map: null
};
const ContactCard = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { contact } = $$props;
  let { selected = false } = $$props;
  let { showActions = true } = $$props;
  createEventDispatcher();
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9)
      return "text-green-600";
    if (confidence >= 0.7)
      return "text-yellow-600";
    return "text-red-600";
  };
  const getStatusColor = (contact2) => {
    if (contact2.is_approved)
      return "bg-green-100 text-green-800";
    if (contact2.is_rejected)
      return "bg-red-100 text-red-800";
    return "bg-yellow-100 text-yellow-800";
  };
  const getStatusText = (contact2) => {
    if (contact2.is_approved)
      return "Approved";
    if (contact2.is_rejected)
      return "Rejected";
    return "Pending";
  };
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric"
    });
  };
  const getContactIcon = (type) => {
    switch (type) {
      case "email":
        return "📧";
      case "phone":
        return "📱";
      case "website":
        return "🌐";
      case "address":
        return "🏠";
      default:
        return "📋";
    }
  };
  if ($$props.contact === void 0 && $$bindings.contact && contact !== void 0)
    $$bindings.contact(contact);
  if ($$props.selected === void 0 && $$bindings.selected && selected !== void 0)
    $$bindings.selected(selected);
  if ($$props.showActions === void 0 && $$bindings.showActions && showActions !== void 0)
    $$bindings.showActions(showActions);
  $$result.css.add(css);
  return `<div class="contact-card bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200 svelte-ktsfxp">
  <div class="flex items-center justify-between p-4 border-b border-gray-100"><div class="flex items-center space-x-3"><input type="checkbox" ${selected ? "checked" : ""} class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
      
      <span class="text-2xl">${escape(getContactIcon(contact.type))}</span>
      
      <div><h3 class="text-sm font-medium text-gray-900 truncate max-w-[200px]">${escape(contact.name)}</h3>
        <p class="text-xs text-gray-500">${escape(contact.position || "Contact")}</p></div></div>

    <div class="flex items-center space-x-2"><span class="${escape(null_to_empty(`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(contact)}`), true) + " svelte-ktsfxp"}">${escape(getStatusText(contact))}</span></div></div>

  
  <div class="p-4 space-y-3">
    ${contact.confidence_score !== void 0 ? `<div class="flex items-center justify-between"><span class="text-xs text-gray-600">Confidence:</span>
        <div class="flex items-center space-x-2"><div class="w-16 bg-gray-200 rounded-full h-2"><div class="h-2 rounded-full bg-gradient-to-r from-red-400 via-yellow-400 to-green-400"${add_attribute("style", `width: ${contact.confidence_score * 100}%`, 0)}></div></div>
          <span class="${escape(null_to_empty(`text-xs font-medium ${getConfidenceColor(contact.confidence_score)}`), true) + " svelte-ktsfxp"}">${escape(Math.round(contact.confidence_score * 100))}%
          </span></div></div>` : ``}

    
    <div class="space-y-1 text-xs">${contact.email ? `<div class="flex justify-between"><span class="text-gray-600">Email:</span>
          <span class="text-gray-900 truncate max-w-[120px]">${escape(contact.email)}</span></div>` : ``}
      
      ${contact.phone ? `<div class="flex justify-between"><span class="text-gray-600">Phone:</span>
          <span class="text-gray-900">${escape(contact.phone)}</span></div>` : ``}
      
      ${contact.company_name ? `<div class="flex justify-between"><span class="text-gray-600">Company:</span>
          <span class="text-gray-900 truncate max-w-[120px]">${escape(contact.company_name)}</span></div>` : ``}</div>

    
    <div class="grid grid-cols-2 gap-2 text-xs">${contact.created_at ? `<div><span class="text-gray-600">Created:</span>
          <div class="text-gray-900">${escape(formatDate(contact.created_at))}</div></div>` : ``}
      
      ${contact.updated_at ? `<div><span class="text-gray-600">Updated:</span>
          <div class="text-gray-900">${escape(formatDate(contact.updated_at))}</div></div>` : ``}</div>

    
    ${contact.metadata && Object.keys(contact.metadata).length > 0 ? `<div class="border-t border-gray-100 pt-2"><div class="text-xs text-gray-600 mb-1">Metadata:</div>
        <div class="grid grid-cols-2 gap-1 text-xs">${each(Object.entries(contact.metadata).slice(0, 4), ([key, value]) => {
    return `<div class="truncate"><span class="text-gray-500">${escape(key)}:</span>
              <span class="text-gray-900 ml-1 truncate">${escape(value)}</span>
            </div>`;
  })}</div></div>` : ``}</div>

  
  ${showActions ? `<div class="flex border-t border-gray-100 divide-x divide-gray-100"><button class="flex-1 py-2 px-3 text-xs text-blue-600 hover:bg-blue-50 transition-colors duration-150" title="View Details">Details
      </button>
      
      <button class="flex-1 py-2 px-3 text-xs text-gray-600 hover:bg-gray-50 transition-colors duration-150" title="Edit Contact">Edit
      </button>
      
      <button class="flex-1 py-2 px-3 text-xs text-red-600 hover:bg-red-50 transition-colors duration-150" title="Delete Contact">Delete
      </button></div>` : ``}
</div>`;
});
const ContactTable_svelte_svelte_type_style_lang = "";
const ContactDetailModal_svelte_svelte_type_style_lang = "";
const BulkOperations = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { selectedCount: selectedCount2 = 0 } = $$props;
  createEventDispatcher();
  if ($$props.selectedCount === void 0 && $$bindings.selectedCount && selectedCount2 !== void 0)
    $$bindings.selectedCount(selectedCount2);
  return `<div class="bg-blue-50 border border-blue-200 rounded-lg p-4"><div class="flex items-center justify-between"><div class="flex items-center space-x-3"><div class="flex-shrink-0"><svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg></div>
      
      <div><h3 class="text-sm font-medium text-blue-800">${escape(selectedCount2)} contact${escape(selectedCount2 !== 1 ? "s" : "")} selected
        </h3>
        <p class="text-sm text-blue-600">Choose an action to perform on all selected contacts
        </p></div></div>

    <div class="flex items-center space-x-2">
      <button ${""} class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed">${``}
        Verify Selected
      </button>

      <button ${""} class="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"><svg class="-ml-1 mr-2 h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
        Export Selected
      </button>

      <button ${""} class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"><svg class="-ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
        Delete Selected
      </button></div></div>

  
  ${``}</div>`;
});
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $selectedCount, $$unsubscribe_selectedCount;
  let $hasPrevPage, $$unsubscribe_hasPrevPage;
  let $hasNextPage, $$unsubscribe_hasNextPage;
  let $totalPages, $$unsubscribe_totalPages;
  let $paginatedContacts, $$unsubscribe_paginatedContacts;
  $$unsubscribe_selectedCount = subscribe(selectedCount, (value) => $selectedCount = value);
  $$unsubscribe_hasPrevPage = subscribe(hasPrevPage, (value) => $hasPrevPage = value);
  $$unsubscribe_hasNextPage = subscribe(hasNextPage, (value) => $hasNextPage = value);
  $$unsubscribe_totalPages = subscribe(totalPages, (value) => $totalPages = value);
  $$unsubscribe_paginatedContacts = subscribe(paginatedContacts, (value) => $paginatedContacts = value);
  let searchTerm = "";
  let { contacts, filteredContacts, selectedContacts, currentPage, itemsPerPage, isLoading, error } = contactStore;
  set_store_value(selectedCount, $selectedCount = selectedCount, $selectedCount);
  set_store_value(paginatedContacts, $paginatedContacts = paginatedContacts, $paginatedContacts);
  set_store_value(totalPages, $totalPages = totalPages, $totalPages);
  set_store_value(hasNextPage, $hasNextPage = hasNextPage, $hasNextPage);
  set_store_value(hasPrevPage, $hasPrevPage = hasPrevPage, $hasPrevPage);
  $$unsubscribe_selectedCount();
  $$unsubscribe_hasPrevPage();
  $$unsubscribe_hasNextPage();
  $$unsubscribe_totalPages();
  $$unsubscribe_paginatedContacts();
  return `<div class="min-h-screen bg-gray-50">
  <div class="bg-white shadow-sm border-b border-gray-200"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="flex justify-between items-center"><div><h1 class="text-2xl font-bold text-gray-900">Contact Management</h1>
          <p class="mt-1 text-sm text-gray-600">Manage and organize your discovered contacts
          </p></div>
        
        <div class="flex items-center space-x-4">
          <div class="flex rounded-md shadow-sm"><button${add_attribute(
    "class",
    `px-3 py-2 text-sm font-medium rounded-l-md ${"bg-blue-100 text-blue-600 border border-blue-200"}`,
    0
  )}>Grid
            </button>
            <button${add_attribute(
    "class",
    `px-3 py-2 text-sm font-medium rounded-r-md ${"bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"}`,
    0
  )}>Table
            </button></div></div></div></div></div>

  
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6"><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div class="lg:col-span-2"><label for="search" class="block text-sm font-medium text-gray-700 mb-1">Search</label>
              <div class="relative"><input id="search" type="text" placeholder="Search contacts..." class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"${add_attribute("value", searchTerm, 0)}>
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"><svg class="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path></svg></div></div></div>

            
            <div><label for="status" class="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select id="status" class="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"><option value="">All Status</option><option value="verified">Verified</option><option value="pending">Pending</option><option value="invalid">Invalid</option></select></div>

            
            <div><label for="confidence" class="block text-sm font-medium text-gray-700 mb-1">Confidence</label>
              <select id="confidence" class="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"><option value="">All Confidence</option><option value="high">High (≥90%)</option><option value="medium">Medium (70-89%)</option><option value="low">Low (&lt;70%)</option></select></div>

            
            <div><label for="agencyType" class="block text-sm font-medium text-gray-700 mb-1">Agency Type</label>
              <select id="agencyType" class="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"><option value="">All Types</option><option value="property_manager">Property Manager</option><option value="landlord">Landlord</option><option value="real_estate_agent">Real Estate Agent</option><option value="broker">Broker</option><option value="developer">Developer</option><option value="other">Other</option></select></div></div>

          
          <div class="mt-4 flex justify-between items-center"><div class="text-sm text-gray-600">Showing ${escape(filteredContacts.length)} of ${escape(contacts.length)} contacts
              ${escape(searchTerm)}</div>
            <button class="text-sm text-gray-600 hover:text-gray-900">Clear all filters
            </button></div></div>

    
    ${$selectedCount > 0 ? `<div class="mb-6">${validate_component(BulkOperations, "BulkOperations").$$render($$result, { selectedCount: $selectedCount }, {}, {})}</div>` : ``}

    
    ${error ? `<div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-md"><div class="flex"><svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>
          <div class="ml-3"><h3 class="text-sm font-medium text-red-800">Error loading contacts</h3>
            <p class="text-sm text-red-600 mt-1">${escape(error)}</p></div></div></div>` : ``}

    
    ${`
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">${each($paginatedContacts, (contact) => {
    return `${validate_component(ContactCard, "ContactCard").$$render(
      $$result,
      {
        contact,
        selected: selectedContacts.has(contact.id.toString())
      },
      {},
      {}
    )}`;
  })}</div>`}

    
    ${$totalPages > 1 ? `<div class="mt-6 flex items-center justify-between"><div class="text-sm text-gray-700">Page ${escape(currentPage)} of ${escape($totalPages)}</div>
        
        <div class="flex space-x-2"><button ${!$hasPrevPage ? "disabled" : ""} class="px-3 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">Previous
          </button>
          
          <button ${!$hasNextPage ? "disabled" : ""} class="px-3 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">Next
          </button></div></div>` : ``}</div></div>


${``}`;
});
export {
  Page as default
};
