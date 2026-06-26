import json
from datetime import datetime, timedelta

def archive_old_threats(threats_file='threats.json', archive_file='archive.json'):
    """Move inactive threats to archive based on clear criteria."""
    
    with open(threats_file, 'r') as f:
        threats = json.load(f)
    
    now = datetime.utcnow()
    archived = []
    active = []
    
    for threat in threats:
        # Criteria for archiving:
        # 1. Status explicitly set to 'resolved' or 'inactive'
        # 2. No evidence updates for 90+ days AND SCP < 0.25
        # 3. Peace agreement confirmed (if domain='military')
        # 4. Disaster officially declared over (if domain='climate')
        
        last_updated = datetime.fromisoformat(threat.get('last_updated', '2000-01-01'))
        days_since_update = (now - last_updated).days
        
        should_archive = False
        
        # Explicit status
        if threat.get('status') in ['resolved', 'inactive', 'peace_agreement', 'disaster_ended']:
            should_archive = True
        
        # Stale + low risk
        if days_since_update > 90 and threat.get('scp', 0) < 0.25:
            should_archive = True
        
        # Peace agreement special case (needs human verification)
        if threat.get('peace_agreement_confirmed', False):
            should_archive = True
        
        if should_archive:
            # Add archive metadata
            threat['archived_date'] = now.isoformat()
            threat['archive_reason'] = get_archive_reason(threat)
            archived.append(threat)
        else:
            active.append(threat)
    
    # Save
    with open(threats_file, 'w') as f:
        json.dump(active, f, indent=2)
    
    # Load existing archive and append
    try:
        with open(archive_file, 'r') as f:
            existing_archive = json.load(f)
    except:
        existing_archive = []
    
    existing_archive.extend(archived)
    
    with open(archive_file, 'w') as f:
        json.dump(existing_archive, f, indent=2)
    
    return len(archived)

def get_archive_reason(threat):
    """Determine why a threat was archived."""
    if threat.get('peace_agreement_confirmed'):
        return 'Peace agreement confirmed'
    if threat.get('status') == 'disaster_ended':
        return 'Disaster officially ended'
    if threat.get('scp', 0) < 0.25:
        return f'Low SCP ({threat.get("scp")}) and inactive for 90+ days'
    return 'Marked as resolved'
