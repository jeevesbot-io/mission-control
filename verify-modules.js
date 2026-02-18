#!/usr/bin/env node

/**
 * Verify that all frontend modules are properly configured
 * Run from project root: node verify-modules.js
 */

import { readdir, readFile } from 'fs/promises';
import { join } from 'path';

const modulesDir = './frontend/src/modules';

async function verifyModules() {
  console.log('🔍 Verifying Mission Control modules...\n');
  
  const modules = await readdir(modulesDir);
  let totalModules = 0;
  let validModules = 0;
  let issues = [];

  for (const moduleName of modules) {
    const routesPath = join(modulesDir, moduleName, 'routes.ts');
    
    try {
      const content = await readFile(routesPath, 'utf-8');
      totalModules++;
      
      // Check for required patterns
      const hasTypeImport = content.includes("import type { RouteRecordRaw } from 'vue-router'");
      const hasRoutesArray = content.match(/const routes: RouteRecordRaw\[\] = \[/);
      const hasModuleExport = content.includes('export default {');
      const hasModuleInfo = content.match(/module: \{[\s\S]*id: ['"](\w+)['"]/);
      const hasRoutesExport = content.includes('routes,') || content.includes('routes:');
      
      if (!hasTypeImport) {
        issues.push(`❌ ${moduleName}: Missing RouteRecordRaw type import`);
      }
      if (!hasRoutesArray) {
        issues.push(`❌ ${moduleName}: Missing routes array declaration`);
      }
      if (!hasModuleExport) {
        issues.push(`❌ ${moduleName}: Missing default export`);
      }
      if (!hasModuleInfo) {
        issues.push(`❌ ${moduleName}: Missing module.id in export`);
      }
      if (!hasRoutesExport) {
        issues.push(`❌ ${moduleName}: Missing routes in export`);
      }
      
      if (hasTypeImport && hasRoutesArray && hasModuleExport && hasModuleInfo && hasRoutesExport) {
        validModules++;
        console.log(`✅ ${moduleName} - OK`);
      }
      
    } catch (err) {
      if (err.code === 'ENOENT') {
        issues.push(`⚠️  ${moduleName}: No routes.ts file found`);
      } else {
        issues.push(`❌ ${moduleName}: Error reading routes.ts - ${err.message}`);
      }
    }
  }
  
  console.log(`\n📊 Summary:`);
  console.log(`   Total modules found: ${totalModules}`);
  console.log(`   Valid modules: ${validModules}`);
  console.log(`   Issues: ${issues.length}`);
  
  if (issues.length > 0) {
    console.log(`\n⚠️  Issues found:\n`);
    issues.forEach(issue => console.log(`   ${issue}`));
    process.exit(1);
  } else {
    console.log(`\n✨ All modules are properly configured!`);
    process.exit(0);
  }
}

verifyModules().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
