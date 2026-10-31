const { execSync } = require('child_process');
const fs = require('fs');

const report = {};

// 1. Tasklist
try {
  report.tasklist = execSync('tasklist | findstr /i "node python"').toString().trim().split('\r\n');
} catch (e) {
  report.tasklist = e.message;
}

// 2. Netstat port 3000
try {
  report.netstat3000 = execSync('netstat -ano | findstr 3000').toString().trim().split('\r\n');
} catch (e) {
  report.netstat3000 = e.message;
}

// 3. PowerShell process details
try {
  const psCmd = 'Get-Process node, python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, Path, StartTime | ConvertTo-Json';
  const out = execSync(`powershell -NoProfile -Command "${psCmd}"`).toString();
  report.processes = JSON.parse(out);
} catch (e) {
  report.processes = e.message;
}

fs.writeFileSync('scripts/diag_out.json', JSON.stringify(report, null, 2), 'utf8');
console.log('Report written to scripts/diag_out.json');
