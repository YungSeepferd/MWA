<script lang="ts">
  import { onMount } from 'svelte';
  
  export let scores: Record<string, number>;
  export let overallScore: number;
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let showLabels: boolean = true;
  export let showValues: boolean = true;
  
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  
  const sizeConfig = {
    small: { width: 200, height: 120, fontSize: 10, padding: 10 },
    medium: { width: 300, height: 180, fontSize: 12, padding: 15 },
    large: { width: 400, height: 240, fontSize: 14, padding: 20 }
  };
  
  const colors = {
    business_context: '#3B82F6',
    market_relevance: '#10B981',
    engagement: '#F59E0B',
    data_completeness: '#8B5CF6',
    source_reliability: '#EF4444'
  };
  
  onMount(() => {
    if (canvas) {
      ctx = canvas.getContext('2d')!;
      drawChart();
    }
  });
  
  function drawChart() {
    const config = sizeConfig[size];
    const { width, height, fontSize, padding } = config;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw background
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, width, height);
    
    // Calculate bar dimensions
    const barCount = Object.keys(scores).length;
    const barWidth = (width - padding * 2) / barCount;
    const maxBarHeight = height - padding * 2 - (showLabels ? fontSize + 5 : 0);
    
    // Draw bars
    Object.entries(scores).forEach(([category, score], index) => {
      const x = padding + index * barWidth;
      const barHeight = score * maxBarHeight;
      const y = height - padding - barHeight;
      
      // Draw bar
      ctx.fillStyle = colors[category as keyof typeof colors] || '#6B7280';
      ctx.fillRect(x, y, barWidth - 2, barHeight);
      
      // Draw value
      if (showValues) {
        ctx.fillStyle = 'white';
        ctx.font = `${fontSize}px system-ui`;
        ctx.textAlign = 'center';
        ctx.fillText(
          `${Math.round(score * 100)}%`,
          x + barWidth / 2,
          y + barHeight / 2 + fontSize / 3
        );
      }
      
      // Draw label
      if (showLabels) {
        ctx.fillStyle = '#374151';
        ctx.font = `${fontSize}px system-ui`;
        ctx.textAlign = 'center';
        const label = category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        ctx.fillText(
          label,
          x + barWidth / 2,
          height - padding + fontSize + 2
        );
      }
    });
    
    // Draw overall score
    if (overallScore !== undefined) {
      ctx.fillStyle = '#1F2937';
      ctx.font = `${fontSize + 2}px system-ui`;
      ctx.textAlign = 'center';
      ctx.fillText(
        `Overall: ${Math.round(overallScore * 100)}%`,
        width / 2,
        padding - 5
      );
    }
  }
  
  $: if (ctx) drawChart();
</script>

<div class="scoring-chart">
  <canvas
    bind:this={canvas}
    width={sizeConfig[size].width}
    height={sizeConfig[size].height}
    class="chart-canvas"
  ></canvas>
</div>

<style>
  .scoring-chart {
    display: inline-block;
    background: white;
    border-radius: var(--radius-lg);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .chart-canvas {
    display: block;
    border-radius: var(--radius-lg);
  }
</style>