import json
data = json.load(open('threats.json'))
threats = data['threats']
print('SCP distribution:')
scps = [t.get('scp', 0) for t in threats]
print(f'Count: {len(scps)}')
print(f'Min: {min(scps):.3f}, Max: {max(scps):.3f}, Avg: {sum(scps)/len(scps):.3f}')
base = [t.get('base_probability', 0) for t in threats]
print(f'Base prob avg: {sum(base)/len(base):.3f}')
for t in threats[:5]:
    print(f"{t.get('id')}: scp={t.get('scp'):.3f}, base={t.get('base_probability'):.3f}")
