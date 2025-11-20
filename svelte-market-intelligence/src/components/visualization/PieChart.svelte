<script lang="ts">
  import { onMount } from 'svelte';
  
  export let data: Record<string, number>;
  export let total: number;
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let showLabels: boolean = true;
  export let showPercentages: boolean = true;
  
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  
  const sizeConfig = {
    small: { width: 200, height: 200, fontSize: 10, padding: 20 },
    medium: { width: 300, height: 300, fontSize: 12, padding: 30 },
    large: { width: 400, height: 400, fontSize: 14, padding: 40 }
  };
  
  const colors = [
    '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444',
    '#84CC16', '#06B6D4', '#F97316', '#8B5CF6', '#EC4899'
  ];
  
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
    
    // Calculate chart dimensions
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) - padding;
    
    // Calculate angles and draw slices
    let startAngle = 0;
    let colorIndex = 0;
    
    Object.entries(data).forEach(([label, value]) => {
      const sliceAngle = (value / total) * 2 * Math.PI;
      const endAngle = startAngle + sliceAngle;
      
      // Draw slice
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      ctx.closePath();
      
      ctx.fillStyle = colors[colorIndex % colors.length];
      ctx.fill();
      
      // Draw label and percentage
      if (showLabels || showPercentages) {
        const midAngle = startAngle + sliceAngle / 2;
        const labelRadius = radius * 0.7;
        const labelX = centerX + Math.cos(midAngle) * labelRadius;
        const labelY = centerY + Math.sin(midAngle) * labelRadius;
        
        ctx.fillStyle = 'white';
        ctx.font = `${fontSize}px system-ui`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        let text = '';
        if (showLabels && showPercentages) {
          const percentage = Math.round((value / total) * 100);
          text = `${label}\n${percentage}%`;
        } else if (showLabels) {
          text = label;
        } else if (showPercentages) {
          const percentage = Math.round((value / total) * 100);
          text = `${percentage}%`;
        }
        
        // Split text into lines
        const lines = text.split('\n');
        lines.forEach((line, index) => {
          ctx.fillText(
            line,
            labelX,
            labelY + (index - (lines.length - 1) / 2) * fontSize
          );
        });
      }
      
      startAngle = endAngle;
      colorIndex++;
    });
    
    // Draw center circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * 0.3, 0, 2 * Math.PI);
    ctx.fillStyle = 'white';
    ctx.fill();
    
    // Draw total in center
    ctx.fillStyle = '#1F2937';
    ctx.font = `${fontSize + 4}px system-ui`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(total.toString(), centerX, centerY);
  }
  
  $: if (ctx) drawChart();
</script>

<div class="pie-chart">
  <canvas
    bind:this={canvas}
    width={sizeConfig[size].width}
    height={sizeConfig[size].height}
    class="chart-canvas"
  ></canvas>
</div>

<style>
  .pie-chart {
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