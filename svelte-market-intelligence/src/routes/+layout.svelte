<script lang="ts">
  import '../app.css';
  import RealTimeNotification from './components/ui/RealTimeNotification.svelte';
  import ErrorBoundary from './components/ui/ErrorBoundary.svelte';
</script>

<svelte:head>
  <title>MWA Market Intelligence</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Market Intelligence Dashboard for MWA - Real-time contact management and analytics">
</svelte:head>

<ErrorBoundary>
  <RealTimeNotification />
  <slot />
</ErrorBoundary>