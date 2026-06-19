#!/bin/bash
cd /home/sad9605/cathedral-core

# Create backup
cp undp-demo.html undp-demo.html.backup

# Replace the Supabase insert with a REST call
python3 - << 'PYEOF'
import re

with open('undp-demo.html', 'r') as f:
    content = f.read()

# Find the Supabase insert block and replace it
pattern = r'if \(supabaseReady && navigator\.onLine\) \{.*?const \{ error \} = await supabase\.from\("reports"\)\.insert\(\{.*?\}\);.*?if \(error\) \{.*?\}'
replacement = '''if (supabaseReady && navigator.onLine) {
  // Direct REST call to Supabase
  const url = 'https://hebioqhjdjtjxjamjvka.supabase.co/rest/v1/reports';
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': 'sb_publishable_eetpDN8_aqWTHr5Bt9ML5w_87XT5ac1',
        'Authorization': 'Bearer sb_publishable_eetpDN8_aqWTHr5Bt9ML5w_87XT5ac1'
      },
      body: JSON.stringify({
        damage_level: report.damage,
        description: report.desc,
        photo: report.photo,
        lat: report.lat,
        lng: report.lng,
        ai_assisted: report.aiAssisted,
        need_help: report.needHelp,
        spotter_id: report.spotterId
      })
    });
    if (!response.ok) {
      const error = await response.json();
      console.warn('Supabase REST error:', error);
      await db.pendingReports.add({ report, timestamp: Date.now(), retryCount: 0 });
    }
  } catch (error) {
    console.warn('Supabase REST error:', error);
    await db.pendingReports.add({ report, timestamp: Date.now(), retryCount: 0 });
  }
} else {
  await db.pendingReports.add({ report, timestamp: Date.now(), retryCount: 0 });
}'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('undp-demo.html', 'w') as f:
    f.write(content)

print('✅ Supabase fix applied')
PYEOF
