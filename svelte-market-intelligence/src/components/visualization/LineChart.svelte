<script lang="ts">
  import { onMount } from 'svelte';
  
  export let data: Array<{ month: string; value: number }>;
  export let title: string = '';
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let showGrid: boolean = true;
  export let showPoints: boolean = true;
  
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  
  const sizeConfig = {
    small: { width: 300, height: 200, fontSize: 10, padding: 20 },
    medium: { width: 400, height: 250, fontSize: 12, padding: 30 },
    large: { width: 500, height: 300, fontSize: 14, padding: 40 }
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
    
    if (!data || data.length === 0) {
      // Draw empty state
      ctx.fillStyle = '#6B7280';
      ctx.font = `${fontSize}px system-ui`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('No data available', width / 2, height / 2);
      return;
    }
    
    // Calculate chart dimensions
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2 - (title ? fontSize + 10 : 0);
    const chartX = padding;
    const chartY = padding + (title ? fontSize + 10 : 0);
    
    // Calculate data range
    const values = data.map(d => d.value);
    const maxValue = Math.max(...values);
    const minValue = Math.min(...values);
    const valueRange = maxValue - minValue || 1;
    
    // Draw title
    if (title) {
      ctx.fillStyle = '#1F2937';
      ctx.font = `${fontSize}px system-ui`;
      ctx.textAlign = 'center';
      ctx.fillText(title, width / 2, padding + fontSize);
    }
    
    // Draw grid
    if (showGrid) {
      ctx.strokeStyle = '#E5E7EB';
      ctx.lineWidth = 1;
      
      // Horizontal grid lines
      const gridLines = 5;
      for (let i = 0; i <= gridLines; i++) {
        const y = chartY + chartHeight - (i / gridLines) * chartHeight;
        ctx.beginPath();
        ctx.moveTo(chartX, y);
        ctx.lineTo(chartX + chartWidth, y);
        ctx.stroke();
        
        // Draw value labels
        const value = minValue + (i / gridLines) * valueRange;
        ctx.fillStyle = '#6B7280';
        ctx.font = `${fontSize - 2}px system-ui`;
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(value).toString(), chartX - 5, y + fontSize / 3);
      }
    }
    
    // Draw axes
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = 2;
    
    // Y-axis
    ctx.beginPath();
    ctx.moveTo(chartX, chartY);
    ctx.lineTo(chartX, chartY + chartHeight);
    ctx.stroke();
    
    // X-axis
    ctx.beginPath();
    ctx.moveTo(chartX, chartY + chartHeight);
    ctx.lineTo(chartX + chartWidth, chartY + chartHeight);
    ctx.stroke();
    
    // Draw line
    ctx.strokeStyle = '#3B82F6';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    data.forEach((point, index) => {
      const x = chartX + (index / (data.length - 1)) * chartWidth;
      const y = chartY + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    ctx.stroke();
    
    // Draw points
    if (showPoints) {
      data.forEach((point, index) => {
        const x = chartX + (index / (data.length - 1)) * chartWidth;
        const y = chartY + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
        
        // Draw point
        ctx.fillStyle = '#3B82F6';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fill();
        
        // Draw value
        ctx.fillStyle = '#1F2937';
        ctx.font = `${fontSize - 2}px system-ui`;
        ctx.textAlign = 'center';
        ctx.fillText(point.value.toString(), x, y - 10);
        
        // Draw month label
        ctx.fillStyle = '#6B7280';
        ctx.fillText(point.month, x, chartY + chartHeight + fontSize);
      });
    }
  }
  
  $: if (ctx) drawChart();
</script>

<div class="line-chart">
  <canvas
    bind:this={canvas}
    width={sizeConfig[size].width}
    height={sizeConfig[size].height}
    class="chart-canvas"
  ></canvas>
</div>

<style>
  .line-chart {
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