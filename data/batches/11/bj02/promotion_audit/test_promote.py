#!/usr/bin/env python3
import copy,hashlib,json,pathlib,unittest
import promote
from verify import verify
T=pathlib.Path('/workspace/blindbox-travel-v20-promoted')
A=T/'data/batches/11/bj02/promotion_audit'
def row(name,area='110105',sid='X'):
 return {'source_entity_id':sid,'full_name':name,'area_code':area,'location':{'lat':None,'lng':None}}
class ConservativeRules(unittest.TestCase):
 def test_park_names_not_erased_to_common_stem(self):
  a,b=row('朝阳公园'),row('海淀公园','110108','Y')
  self.assertNotEqual(promote.proper_key(a['full_name']),promote.proper_key(b['full_name']))
  self.assertEqual(promote.collision_flags(a,[b],[]),[])
 def test_same_name_different_district_is_review_not_merge(self):
  a,b=row('人民公园'),row('人民公园','110108','Y')
  self.assertEqual(promote.identity_action(a,b),'review_cross_district')
  self.assertEqual(promote.identity_action(a,b,True),'review_cross_district')
  self.assertEqual(len(promote.collision_flags(a,[b],[])),1)
 def test_missing_coordinates_reserved(self):
  self.assertEqual(promote.identity_action(row('朝阳公园'),row('朝阳公园',sid='Y')),'review_missing_coordinates')
 def test_synonyms_not_automatic(self):
  self.assertEqual(promote.identity_action(row('野鸭湖景区'),row('野鸭湖国家湿地公园',sid='Y')),'review_missing_coordinates')
 def test_empty_fallback_never_global_key(self):
  self.assertEqual(promote.containment_key('公园'),'')
  self.assertEqual(promote.proper_key('北京景区'),'')
  self.assertEqual(promote.identity_action(row('北京景区'),row('北京景区',sid='Y')),'review_empty_key')
  self.assertEqual(promote.collision_flags(row('朝阳公园'),[row('公园',sid='Y')],[]),[])
 def test_latin_casefold_and_unicode_are_only_syntactic(self):
  self.assertEqual(promote.strict_name(' ＡＢＣ  Museum '),'abcmuseum')
  self.assertNotEqual(promote.proper_key('朝阳公园'),promote.proper_key('朝阳'))
 def test_official_assertion_is_catalog_link_not_geomerge(self):
  self.assertEqual(promote.identity_action(row('北京园博园景区'),row('北京园博园',sid='Y'),True),'link_official_catalog_assertion_not_geo_merge')
 def test_null_district_never_authorizes_merge(self):
  self.assertFalse(promote.compatible_area(row('同名',None),row('同名')))
  self.assertEqual(promote.identity_action(row('同名',None),row('同名')),'review_missing_coordinates')
 def test_parent_child_preserved_both_directions(self):
  m=promote.load(T/'data/national_spots_master.json');by={r['spot_id']:r for r in m};c=[r for r in m if r.get('catalog_relation')=='child_of'];self.assertEqual(len(c),6)
  for r in c:self.assertIn(r['spot_id'],[a['spot_id'] for a in by[r['parent_spot_id']]['sub_spots']])
 def test_shared_detail_url_not_automatic_alias(self):
  rows=promote.load(A/'all_338_decisions.json');by={r['source_entity_id']:r for r in rows}
  # Museum may be a separate hall; shared generic temple URL is not identity proof.
  self.assertEqual(by['BJ02_MUSEUMS_0036']['outcome'],'review')
  self.assertEqual(by['BJ02_MUSEUMS_0064']['outcome'],'review')
 def test_management_relation_not_spatial_identity(self):
  rows=promote.load(A/'all_338_decisions.json');by={r['source_entity_id']:r for r in rows}
  self.assertEqual(by['BJ02_SCENIC_0020']['outcome'],'promoted_new_catalog')
  self.assertEqual(by['BJ02_MUSEUMS_0024']['outcome'],'review')
 def test_memorial_museum_not_sculpture_park(self):
  m=promote.load(T/'data/national_spots_master.json');by={r['source_entity_id']:r for r in m}
  self.assertIn('BJ02_SCENIC_0026',by);self.assertIn('BJ_PARKS_2026_0447',by)
  self.assertNotEqual(by['BJ02_SCENIC_0026']['spot_id'],by['BJ_PARKS_2026_0447']['spot_id'])
 def test_unknown_child_stays_city_only(self):
  n=promote.load(A/'promoted_catalog_entities.json');unknown=[r for r in n if not r['area_code']];self.assertEqual(len(unknown),5)
  counties=[r for f in (T/'data/areas_db/11').glob('*.json') for r in promote.load(f)]
  self.assertTrue({r['spot_id'] for r in unknown}.isdisjoint({r['spot_id'] for r in counties}))
 def test_whole_snapshot_verification(self):self.assertEqual(verify(T)['structure_errors'],0)
 def test_z_idempotent_full_materialization(self):
  paths=[T/'data/national_spots_master.json',T/'data/evolution_metrics.json',T/'data/cities_db/11_1101.json',T/'data/cities_db/index.json',T/'data/areas_db/index.json']+list((T/'data/areas_db/11').glob('*.json'))+[A/n for n in ['report.json','all_338_decisions.json','all_408_observation_dispositions.json','route_node_review.json']]
  before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
  promote.run('/workspace/blindbox-travel-v20',T,A)
  self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
if __name__=='__main__':unittest.main(verbosity=2)
