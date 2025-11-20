<script lang="ts">
  const menuItems = [
    { label: 'Dashboard', icon: '🏠', href: '/' },
    { label: 'Search', icon: '🔍', href: '/search' },
    { label: 'Contacts', icon: '👥', href: '/contacts' },
    { label: 'Analytics', icon: '📊', href: '/analytics' }
  ];
</script>

<nav class="mobile-nav">
  <div class="flex justify-between items-center">
    {#each menuItems as item}
      <a
        href={item.href}
        class="flex flex-col items-center p-2 text-sm text-gray-600 hover:text-primary-600 transition-colors"
      >
        <span class="text-lg mb-1">{item.icon}</span>
        <span class="text-xs">{item.label}</span>
      </a>
    {/each}
  </div>
</nav>

<style>
  .mobile-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-top: 1px solid var(--gray-200);
    padding: var(--space-2);
    z-index: 1000;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  }

  .flex {
    display: flex;
  }

  .justify-between {
    justify-content: space-between;
  }

  .items-center {
    align-items: center;
  }

  .flex-col {
    flex-direction: column;
  }

  .p-2 {
    padding: var(--space-2);
  }

  .text-sm {
    font-size: var(--font-size-sm);
  }

  .text-lg {
    font-size: var(--font-size-lg);
  }

  .text-xs {
    font-size: var(--font-size-xs);
  }

  .text-gray-600 {
    color: var(--gray-600);
  }


  .hover\\:text-primary-600:hover {
    color: var(--primary-600);
  }

  .transition-colors {
    transition: color 0.2s ease;
  }

  .mb-1 {
    margin-bottom: var(--space-1);
  }


  /* Touch feedback */
  a {
    -webkit-tap-highlight-color: transparent;
    border-radius: var(--radius-md);
    transition: background-color 0.2s ease;
  }

  a:active {
    background-color: var(--gray-100);
  }
</style>