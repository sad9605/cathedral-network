#!/usr/bin/env python3
"""
add_descriptions.py – Add descriptions to top-priority threats in threats.json.
Run once, then commit.
"""

import json
from pathlib import Path

THREATS_FILE = "threats.json"

# Descriptions for the top 20 threats (by priority score)
DESCRIPTIONS = {
    "C01": "Geopolitical conflict involving Iran, Israel, and the US, with potential closure of the Strait of Hormuz, disrupting global oil supplies and triggering a wider regional war. Elevated risk of missile strikes and naval engagements.",
    "C-USIRAN": "Direct military confrontation between the United States and Iran, following proxy escalations and missile strikes. Includes the possibility of US airstrikes on Iranian nuclear sites and Iranian retaliation against US bases in the region.",
    "C-BELT": "Iran's 'Resistance Security Belt' strategy – a network of proxy forces (Hezbollah, Houthis, Hamas) coordinating asymmetric attacks across the Middle East, threatening shipping lanes and US allies.",
    "C-RED-BLOCK": "Blockade or disruption of the Bab el-Mandeb strait by Houthi forces, threatening global shipping and oil tankers. Could trigger a broader naval conflict and increase insurance premiums.",
    "C132": "Great power entanglement involving the US, Iran, Russia, and China. Escalation in one theater risks drawing in multiple major powers, potentially leading to a wider conflict beyond the Middle East.",
    "C129": "Renewed armed conflict between Armenia and Azerbaijan over the Nagorno-Karabakh region, risking regional instability, refugee flows, and involvement of Russia and Turkey.",
    "C54": "Baltic Grey-Zone operations – Russian hybrid warfare including GPS jamming, cyber attacks, and intimidation of NATO allies. Risks triggering NATO Article 5 if incidents escalate.",
    "C88": "Taiwan Strait Incident Risk – increased Chinese military activity and US naval patrols, raising the probability of a miscalculation or accidental clash that could escalate rapidly.",
    "C90": "South China Sea Militarisation – China's expansion of artificial islands and military presence, increasing tensions with the Philippines, Vietnam, and the US. Risk of skirmishes.",
    "C48": "AI Deepfake Operations – coordinated disinformation campaigns using generative AI to manipulate public opinion, disrupt elections, and undermine trust in democratic institutions.",
    "C19": "Zaporizhzhia Nuclear Power Plant – ongoing shelling and military activity around Europe's largest nuclear plant, risking a radiation leak or catastrophic meltdown, with regional fallout.",
    "C25": "NATO Article 4 (Romania) – potential activation by Romania due to Russian drone or missile incursions, bringing NATO allies into direct consultation and potentially collective defence.",
    "C3": "Ukraine-Russia Spillover – the war extends beyond Ukraine's borders, affecting neighbouring NATO states through missile strikes, drone incursions, or refugee surges.",
    "C11": "Iraq Instability – resurgence of ISIS, Shia militias, and political deadlock, threatening oil infrastructure and regional security, and potentially drawing in US and Iranian forces.",
    "C58": "Underwater Infrastructure Sabotage – suspected Russian attacks on undersea cables, gas pipelines, and internet cables, disrupting global communications and energy supplies.",
    "C64": "Mediterranean Migration – increased irregular migration flows from North Africa and the Middle East, straining EU border states, fuelling populism, and creating humanitarian crises.",
    "C85": "Cartel Violence Mexico – intensified fighting between drug cartels, leading to mass casualties, displacement, and potential spillover into the US, affecting border security.",
    "C122": "North Korea Ballistic – North Korea tests ICBMs capable of reaching the US, raising tensions, triggering sanctions, and risking military response from the US and South Korea.",
    "C2": "Information Warfare – state-sponsored propaganda, disinformation, and cyber campaigns targeting public trust, elections, and geopolitical narratives globally.",
    "C4": "Moldova Transnistria escalation – Russia-backed separatists in Transnistria may provoke a crisis, threatening Moldova's security and potentially drawing in NATO and Russia.",
}

def main():
    data = load_json(THREATS_FILE)
    if not data:
        print("❌ Could not load threats.json")
        return

    threats = data.get('threats', [])
    updated = 0

    for t in threats:
        tid = t.get('id')
        if tid in DESCRIPTIONS:
            # Only set if not already present or empty
            if not t.get('description') or t['description'] == '':
                t['description'] = DESCRIPTIONS[tid]
                updated += 1

    save_json(data, THREATS_FILE)
    print(f"✅ Added descriptions to {updated} threats.")

if __name__ == "__main__":
    main()
