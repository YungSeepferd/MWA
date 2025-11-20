<script lang="ts">
  export let type: 'card' | 'text' | 'circle' | 'button' = 'card';
  export let height: string = 'auto';
  export let width: string = '100%';
  export let className: string = '';

  const getSkeletonClass = () => {
    const baseClass = 'skeleton rounded';
    
    switch (type) {
      case 'card':
        return `${baseClass} h-full`;
      case 'text':
        return `${baseClass} h-4`;
      case 'circle':
        return `${baseClass} rounded-full aspect-square`;
      case 'button':
        return `${baseClass} h-10`;
      default:
        return baseClass;
    }
  };
</script>

<div
  class={`${getSkeletonClass()} ${className}`}
  style="height: {height}; width: {width};"
></div>

<style>
  .skeleton {
    background: linear-gradient(90deg, var(--gray-200) 25%, var(--gray-300) 50%, var(--gray-200) 75%);
    background-size: 200% 100%;
    animation: loading 1.5s infinite;
  }

  .rounded {
    border-radius: var(--radius-md);
  }

  .rounded-full {
    border-radius: 50%;
  }

  .h-full {
    height: 100%;
  }

  .h-4 {
    height: 1rem;
  }

  .h-10 {
    height: 2.5rem;
  }

  .aspect-square {
    aspect-ratio: 1 / 1;
  }

  @keyframes loading {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
</style>