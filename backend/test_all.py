from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)

# Health
r = c.get('/api/health')
assert r.status_code == 200, 'health failed'
h = r.json()['result']
print(f'Health: {h["ai_provider"]} | demo: {h["demo_mode"]} | features: {len(h["features"])}')

# Safety
r = c.post('/api/safety/analyze', data={'description':'worker near slab edge no helmet','project_type':'residential','location':'Level 2','work_activity':'slab work'})
assert r.status_code == 200, 'safety failed'
print(f'Safety: risk={r.json()["result"]["risk_level"]} | provider={r.json()["meta"]["provider"]}')

# Planning
r = c.post('/api/planning/plan', json={'project_type':'residential','built_up_area_sqft':2500,'floors':2,'location':'Pune','quality':'standard','start_date':'2026-11-01','currency':'INR'})
assert r.status_code == 200, 'planning failed'
print(f'Planning: cost={r.json()["result"]["cost"]["total"]} | duration={r.json()["result"]["schedule"]["total_duration_days"]} days')

# Valuation
r = c.post('/api/valuation/estimate', json={'property_type':'apartment','city':'Pune','area_sqft':1200,'age_years':5,'bedrooms':2,'quality':'premium','condition':'good','amenities':['parking','lift'],'currency':'INR'})
assert r.status_code == 200, 'valuation failed'
res = r.json()['result']
print(f'Valuation: INR {res["estimated_value"]:,} | range: INR {res["value_range_low"]:,}-INR {res["value_range_high"]:,}')

# Assistant
r = c.post('/api/assistant/chat', json={'message':'How to recover schedule delay?','project_context':{'project_type':'commercial','stage':'structure','location':'Pune'}})
assert r.status_code == 200, 'assistant failed'
print(f'Assistant: answer_len={len(r.json()["result"]["answer"])} | actions={len(r.json()["result"]["action_items"])}')

# Knowledge
r = c.post('/api/knowledge/ask', json={'question':'concrete curing period','topic':'concrete','experience_level':'intermediate'})
assert r.status_code == 200, 'knowledge failed'
print(f'Knowledge: answer_len={len(r.json()["result"]["answer"])} | refs={len(r.json()["result"]["references"])}')

# Weather
r = c.get('/api/weather/advisory', params={'city':'Pune'})
assert r.status_code == 200, 'weather failed'
print(f'Weather: {r.json()["result"]["data_source"]} | {r.json()["result"]["current"]["temperature_c"]}°C')

print()
print('ALL 7 BACKEND MODULES WORKING')
