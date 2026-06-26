import json
import re
from datetime import datetime

class ThreatScanner:
    """Scan OSINT feeds for emerging threats not yet tracked."""
    
    def __init__(self, feeds_file='sweep_report.json'):
        with open(feeds_file, 'r') as f:
            self.feeds = json.load(f)
        
        # Keywords that signal a potential new threat
        self.keywords = {
            'military': ['war', 'conflict', 'troop movement', 'mobilization', 'deployment', 
                         'skirmish', 'border clash', 'ceasefire violated', 'act of war'],
            'climate': ['flood', 'wildfire', 'drought', 'cyclone', 'hurricane', 'heatwave',
                        'famine', 'crop failure', 'water scarcity', 'extreme weather'],
            'economic': ['crash', 'collapse', 'bankruptcy', 'hyperinflation', 'default',
                         'sanctions', 'embargo', 'supply chain disruption', 'shortage'],
            'cyber': ['breach', 'ransomware', 'outage', 'DDoS', 'cyber attack', 'data leak',
                      'critical infrastructure', 'zero-day', 'compromised'],
            'health': ['outbreak', 'epidemic', 'pandemic', 'quarantine', 'new variant',
                       'vaccine failure', 'health emergency', 'hospital collapse'],
            'social': ['protest', 'riot', 'civil unrest', 'strike', 'demonstration',
                       'uprising', 'government collapse', 'coup attempt']
        }
    
    def scan_for_new_threats(self, existing_threats_file='threats.json'):
        """Check OSINT feeds for potential threats not in threats.json."""
        
        with open(existing_threats_file, 'r') as f:
            existing = json.load(f)
        
        existing_names = [t.get('name', '').lower() for t in existing]
        existing_regions = [t.get('region', '').lower() for t in existing]
        
        candidates = []
        
        for feed_item in self.feeds.get('items', []):
            text = feed_item.get('title', '') + ' ' + feed_item.get('description', '')
            text_lower = text.lower()
            
            # Check for keywords
            matched_domains = []
            for domain, words in self.keywords.items():
                for word in words:
                    if word in text_lower:
                        matched_domains.append(domain)
            
            if matched_domains:
                # Extract potential threat name (simple heuristic)
                name = self._extract_name(text)
                region = self._extract_region(text)
                
                # Skip if already tracked
                if name.lower() in existing_names:
                    continue
                if region.lower() in existing_regions and len(matched_domains) < 2:
                    continue
                
                candidates.append({
                    'name': name,
                    'region': region,
                    'domains': list(set(matched_domains)),
                    'evidence': text[:200],
                    'source': feed_item.get('source', 'unknown'),
                    'date_detected': datetime.utcnow().isoformat(),
                    'confidence': self._calculate_confidence(matched_domains, text)
                })
        
        return candidates
    
    def _extract_name(self, text):
        """Extract potential threat name from text."""
        # Look for patterns like "Crisis in X" or "X conflict"
        patterns = [
            r'crisis in (\w+)',
            r'conflict in (\w+)',
            r'war in (\w+)',
            r'(\w+) crisis',
            r'(\w+) conflict',
            r'(\w+) emergency',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).capitalize()
        return 'Unnamed threat'
    
    def _extract_region(self, text):
        """Extract region from text."""
        # Simple: look for country names
        countries = ['Ukraine', 'Russia', 'Sudan', 'Gaza', 'Israel', 'Syria', 'Yemen', 
                     'Afghanistan', 'Myanmar', 'Ethiopia', 'Haiti', 'Venezuela']
        for country in countries:
            if country.lower() in text.lower():
                return country
        return 'Unknown'
    
    def _calculate_confidence(self, matched_domains, text):
        """Calculate confidence score for a potential threat."""
        # More domains = higher confidence
        domain_score = min(1.0, len(matched_domains) * 0.3)
        # More keywords = higher confidence
        keyword_count = sum(1 for word in self.keywords.values() for w in word if w in text.lower())
        keyword_score = min(1.0, keyword_count * 0.05)
        return min(1.0, (domain_score + keyword_score) / 2)
