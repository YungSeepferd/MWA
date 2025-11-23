/**
 * Legacy Dashboard Migration Analysis Tool
 * Phase 1: Analysis & Baseline Creation
 * 
 * This tool analyzes the legacy dashboard codebase and creates a comprehensive
 * feature inventory using the Shopify Deprecation Toolkit methodology.
 */

const fs = require('fs');
const path = require('path');

class MigrationAnalyzer {
  constructor() {
    this.analysisResults = {
      files: [],
      totalLines: 0,
      features: [],
      components: [],
      dependencies: [],
      metrics: {}
    };
    
    // Security: Initialize HTML escaping function
    this.escapeHtml = this.createEscapeHtmlFunction();
  }

  /**
   * Analyze a single file and extract features
   */
  analyzeFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n').length;
      const fileName = path.basename(filePath);
      const fileType = path.extname(filePath);
      
      const fileAnalysis = {
        path: filePath,
        name: fileName,
        type: fileType,
        lines: lines,
        features: this.extractFeatures(content, fileName),
        dependencies: this.extractDependencies(content, fileType)
      };
      
      this.analysisResults.files.push(fileAnalysis);
      this.analysisResults.totalLines += lines;
      
      return fileAnalysis;
    } catch (error) {
      console.error(`Error analyzing file ${filePath}:`, error.message);
      return null;
    }
  }

  /**
   * Extract features from file content based on patterns
   */
  extractFeatures(content, fileName) {
    const features = [];
    
    // JavaScript function patterns
    const functionPatterns = [
      { pattern: /function\s+(\w+)\s*\(/g, type: 'function' },
      { pattern: /const\s+(\w+)\s*=\s*\([^)]*\)\s*=>/g, type: 'arrow-function' },
      { pattern: /class\s+(\w+)/g, type: 'class' },
      { pattern: /async\s+function\s+(\w+)/g, type: 'async-function' }
    ];
    
    // HTML template patterns
    const htmlPatterns = [
      { pattern: /<div[^>]*id="([^"]+)"/g, type: 'element' },
      { pattern: /<script[^>]*>([\s\S]*?)<\/script>/g, type: 'inline-script' },
      { pattern: /onclick="([^"]+)"/g, type: 'event-handler' }
    ];
    
    // API endpoint patterns
    const apiPatterns = [
      { pattern: /fetch\(['"]([^'"]+)['"]/g, type: 'api-call' },
      { pattern: /\/api\/v1\/([^'"]+)/g, type: 'api-endpoint' }
    ];
    
    let patterns = [];
    
    if (fileName.endsWith('.js')) {
      patterns = [...functionPatterns, ...apiPatterns];
    } else if (fileName.endsWith('.html')) {
      patterns = [...htmlPatterns, ...apiPatterns];
    }
    
    patterns.forEach(({ pattern, type }) => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        features.push({
          name: match[1],
          type: type,
          context: this.getContext(content, match.index)
        });
      }
    });
    
    return features;
  }

  /**
   * Extract dependencies from file content
   */
  extractDependencies(content, fileType) {
    const dependencies = [];
    
    if (fileType === '.js') {
      // CDN dependencies
      const cdnPattern = /https:\/\/cdn\.jsdelivr\.net[^"']+/g;
      let match;
      while ((match = cdnPattern.exec(content)) !== null) {
        dependencies.push({
          type: 'cdn',
          url: match[0],
          category: 'external'
        });
      }
      
      // Library references
      const libPatterns = [
        { pattern: /bootstrap\./g, name: 'Bootstrap' },
        { pattern: /Chart\./g, name: 'Chart.js' },
        { pattern: /jQuery|\$/g, name: 'jQuery' }
      ];
      
      libPatterns.forEach(({ pattern, name }) => {
        if (pattern.test(content)) {
          dependencies.push({
            type: 'library',
            name: name,
            category: 'frontend'
          });
        }
      });
    }
    
    return dependencies;
  }

  /**
   * Get context around a feature match
   */
  getContext(content, index, contextLines = 3) {
    const lines = content.split('\n');
    let lineNumber = 0;
    let currentIndex = 0;
    
    for (let i = 0; i < lines.length; i++) {
      currentIndex += lines[i].length + 1; // +1 for newline
      if (currentIndex > index) {
        lineNumber = i + 1;
        break;
      }
    }
    
    const start = Math.max(0, lineNumber - contextLines - 1);
    const end = Math.min(lines.length, lineNumber + contextLines);
    
    return {
      line: lineNumber,
      snippet: lines.slice(start, end).join('\n')
    };
  }

  /**
   * Analyze the entire dashboard directory
   */
  analyzeDashboard(dashboardPath = './dashboard') {
    console.log('🔍 Analyzing legacy dashboard codebase...');
    
    const files = this.getFilesRecursive(dashboardPath);
    
    files.forEach(file => {
      this.analyzeFile(file);
    });
    
    this.aggregateResults();
    this.generateReport();
    
    return this.analysisResults;
  }

  /**
   * Get all files recursively from a directory
   */
  getFilesRecursive(dir) {
    let results = [];
    const list = fs.readdirSync(dir);
    
    list.forEach(file => {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      
      if (stat && stat.isDirectory()) {
        results = results.concat(this.getFilesRecursive(filePath));
      } else {
        // Only analyze relevant file types
        if (file.endsWith('.js') || file.endsWith('.html') || file.endsWith('.css')) {
          results.push(filePath);
        }
      }
    });
    
    return results;
  }

  /**
   * Aggregate analysis results
   */
  aggregateResults() {
    const { files } = this.analysisResults;
    
    // Aggregate features
    const allFeatures = files.flatMap(file => file.features);
    this.analysisResults.features = allFeatures;
    
    // Aggregate components (unique feature types)
    const componentTypes = [...new Set(allFeatures.map(f => f.type))];
    this.analysisResults.components = componentTypes.map(type => ({
      type: type,
      count: allFeatures.filter(f => f.type === type).length,
      examples: allFeatures.filter(f => f.type === type).slice(0, 3)
    }));
    
    // Aggregate dependencies
    const allDeps = files.flatMap(file => file.dependencies);
    const uniqueDeps = [...new Map(allDeps.map(dep => [dep.name || dep.url, dep])).values()];
    this.analysisResults.dependencies = uniqueDeps;
    
    // Calculate metrics
    this.analysisResults.metrics = {
      totalFiles: files.length,
      totalLines: this.analysisResults.totalLines,
      totalFeatures: allFeatures.length,
      uniqueComponents: componentTypes.length,
      externalDependencies: uniqueDeps.filter(d => d.category === 'external').length,
      averageFileSize: Math.round(this.analysisResults.totalLines / files.length)
    };
  }

  /**
   * Generate comprehensive analysis report
   */
  generateReport() {
    const { metrics, components, dependencies, files } = this.analysisResults;
    
    console.log('\n📊 LEGACY DASHBOARD ANALYSIS REPORT');
    console.log('='.repeat(50));
    
    console.log('\n📈 METRICS:');
    console.log(`Total Files: ${metrics.totalFiles}`);
    console.log(`Total Lines: ${metrics.totalLines}`);
    console.log(`Total Features: ${metrics.totalFeatures}`);
    console.log(`Unique Components: ${metrics.uniqueComponents}`);
    console.log(`External Dependencies: ${metrics.externalDependencies}`);
    console.log(`Average File Size: ${metrics.averageFileSize} lines`);
    
    console.log('\n🏗️ COMPONENTS:');
    components.forEach(comp => {
      console.log(`- ${comp.type}: ${comp.count} instances`);
    });
    
    console.log('\n🔗 DEPENDENCIES:');
    dependencies.forEach(dep => {
      console.log(`- ${dep.name || dep.url} (${dep.type}, ${dep.category})`);
    });
    
    console.log('\n📁 FILES (Top 10 by size):');
    files
      .sort((a, b) => b.lines - a.lines)
      .slice(0, 10)
      .forEach(file => {
        console.log(`- ${file.name}: ${file.lines} lines, ${file.features.length} features`);
      });
    
    // Save detailed report to file
    this.saveDetailedReport();
  }

  /**
   * Save detailed analysis to JSON file
   */
  saveDetailedReport() {
    const report = {
      timestamp: new Date().toISOString(),
      analysis: this.analysisResults
    };
    
    fs.writeFileSync(
      './migration-analysis-report.json',
      JSON.stringify(report, null, 2)
    );
    
    console.log('\n💾 Detailed report saved to: migration-analysis-report.json');
  }

  /**
   * Create feature mapping for Svelte migration
   */
  createFeatureMapping() {
    const mapping = {
      legacyFeatures: this.analysisResults.features,
      svelteEquivalents: this.mapToSvelteComponents(),
      migrationPriority: this.calculateMigrationPriority()
    };
    
    fs.writeFileSync(
      './feature-mapping.json',
      JSON.stringify(mapping, null, 2)
    );
    
    console.log('🗺️ Feature mapping saved to: feature-mapping.json');
    return mapping;
  }

  /**
   * Map legacy features to Svelte components
   */
  mapToSvelteComponents() {
    const mapping = {};
    
    this.analysisResults.features.forEach(feature => {
      mapping[feature.name] = {
        legacyType: feature.type,
        svelteComponent: this.suggestSvelteComponent(feature),
        complexity: this.assessComplexity(feature),
        estimatedEffort: this.estimateEffort(feature)
      };
    });
    
    return mapping;
  }

  /**
   * Suggest appropriate Svelte component for legacy feature
   */
  suggestSvelteComponent(feature) {
    const mappings = {
      'function': 'Svelte component method',
      'arrow-function': 'Svelte component method',
      'class': 'Svelte store or class',
      'async-function': 'Svelte async method with loading states',
      'api-call': 'Svelte service function',
      'api-endpoint': 'API route handler',
      'element': 'Svelte component',
      'event-handler': 'Svelte event handler'
    };
    
    return mappings[feature.type] || 'Custom Svelte component';
  }

  /**
   * Assess complexity of a feature
   */
  assessComplexity(feature) {
    const context = feature.context.snippet;
    let complexity = 'low';
    
    if (context.includes('async') || context.includes('await')) complexity = 'medium';
    if (context.includes('fetch') || context.includes('API')) complexity = 'high';
    if (context.length > 200) complexity = 'high';
    
    return complexity;
  }

  /**
   * Estimate effort for migration
   */
  estimateEffort(feature) {
    const complexity = this.assessComplexity(feature);
    const efforts = { low: 1, medium: 3, high: 8 };
    return efforts[complexity];
  }

  /**
   * Calculate migration priority based on complexity and usage
   */
  calculateMigrationPriority() {
    const features = this.analysisResults.features;
    const usageCount = {};
    
    // Count usage of each feature
    features.forEach(feature => {
      usageCount[feature.name] = (usageCount[feature.name] || 0) + 1;
    });
    
    return features.map(feature => ({
      name: feature.name,
      type: feature.type,
      usage: usageCount[feature.name],
      complexity: this.assessComplexity(feature),
      effort: this.estimateEffort(feature),
      priority: this.calculatePriorityScore(feature, usageCount[feature.name])
    })).sort((a, b) => b.priority - a.priority);
  }

  /**
   * Calculate priority score for migration
   */
  calculatePriorityScore(feature, usage) {
    const complexityScores = { low: 1, medium: 3, high: 5 };
    return complexityScores[feature.complexity] * usage;
  }
  }

  /**
   * Create HTML escaping function to prevent XSS
   */
  createEscapeHtmlFunction() {
    const map = {
      '&': '&',
      '<': '<',
      '>': '>',
      '"': '"',
      "'": '&#x27;',
      '/': '&#x2F;'
    };
    
    return function(text) {
      if (typeof text !== 'string') {
        return text;
      }
      return text.replace(/[&<>"'/]/g, (char) => map[char]);
    };
  }

// Export for use in other scripts
module.exports = MigrationAnalyzer;

// Run analysis if script is executed directly
if (require.main === module) {
  const analyzer = new MigrationAnalyzer();
  analyzer.analyzeDashboard();
  analyzer.createFeatureMapping();
}