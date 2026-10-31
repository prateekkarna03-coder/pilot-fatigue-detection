const { execSync } = require('child_process');

try {
  const psCmd = 'Get-Process | Where-Object { $_.ProcessName -like "*python*" } | Select-Object Id, ProcessName, Path | ConvertTo-Json';
  const out = execSync(`powershell -NoProfile -Command "${psCmd.replace(/\$/g, '`$')}"`).toString();
  console.log('Python processes:\n', out);
} catch (e) {
  console.log('Error querying python processes:', e.message);
}
