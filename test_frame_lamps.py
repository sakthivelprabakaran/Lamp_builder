import unittest
import numpy as np
import frame_lamps as f
class FrameGeometryTests(unittest.TestCase):
 def test_separate_leg_and_light_heights(self):
  for leg in (914.4,1066.8,1219.2):
   p=f.resolve(dict(standing=True,exposed_leg_height=leg))
   self.assertAlmostEqual(p['height'],leg+304.8)
   self.assertAlmostEqual(p['panel_bottom'],leg)
   self.assertLessEqual(p['segment_height'],230)
 def test_panel_clearances_and_flat_gate(self):
  p=f.resolve(dict(standing=True,exposed_leg_height=1066.8))
  self.assertGreater(p['socket_mm'],p['rod_mm'])
  self.assertGreater(p['slot_mm'],p['panel_mm'])
  v,faces,_=f.panel(p)
  checked=f.check_part(v,faces)
  self.assertTrue(checked['screen']['passed'])
  self.assertLessEqual(float(np.ptp(v,axis=0).max()),250)
 def test_retaining_cap_closed(self):
  v,faces=f.stop_cap({})
  self.assertTrue(f.check_part(v,faces)['screen']['passed'])
 def test_standing_preview_only_top_foot(self):
  d=f.preview(dict(standing=True,exposed_leg_height=1219.2))
  v=np.array(d['vertices']).reshape(-1,3)
  self.assertAlmostEqual(v[:,2].min(),1219.2,places=3)
  self.assertAlmostEqual(v[:,2].max()-v[:,2].min(),304.8,places=3)
  self.assertEqual(len(d['structure']['wood_rails']),8)
  self.assertTrue(all(r['start'][2]==r['end'][2] for r in d['structure']['wood_rails']))
  self.assertEqual(d['structure']['foot_caps'],4)
  self.assertFalse(d['structure']['physical_stability_verified'])
 def test_dovetail_exact_profiles(self):
  for fn in (f.dovetail_female,f.dovetail_male):
   v,faces=fn({})
   ok,metrics=f.engine.verify_mesh(v,faces)
   self.assertTrue(ok)
   self.assertTrue(metrics['single_piece'])
   self.assertLessEqual(float(np.ptp(v,axis=0).max()),250)
 def test_simple_joint_inventory(self):
  items=f.joint_instances(dict(standing=True,exposed_leg_height=1066.8))
  self.assertEqual(sum(i['part']=='female' for i in items),8)
  self.assertEqual(sum(i['part']=='male' for i in items),16)
  self.assertEqual(sum(i['part']=='post-wedge' for i in items),0)
  self.assertEqual(sum(i['part']=='post-pad' for i in items),0)
  self.assertEqual(set(i['part'] for i in items),{'female','male'})
  self.assertEqual(len(f.joint_instances(dict(standing=True,exposed_leg_height=1066.8),legacy=True)),40)
 def test_latest_standing_preview_interfaces(self):
  for leg in (914.4,1066.8,1219.2):
   d=f.preview(dict(standing=True,width=220,exposed_leg_height=leg))
   latest=d['latest_parts'];self.assertTrue(latest['available'])
   self.assertEqual(set(d['joints']),{'female','male'})
   self.assertEqual(sum(i['part']=='bottom-holder'for i in latest['instances']),4)
   tray=next(i for i in latest['instances']if i['part']=='tray')
   self.assertAlmostEqual(tray['xyz'][2],leg)
   for data in [*d['joints'].values(),*latest['meshes'].values()]:
    ok,_=f.engine.verify_mesh(np.array(data['vertices']).reshape(-1,3),np.array(data['indices']).reshape(-1,3));self.assertTrue(ok)
  unsupported=f.preview(dict(standing=True,width=210,exposed_leg_height=1066.8))
  self.assertFalse(unsupported['latest_parts']['available'])
  self.assertIsNone(unsupported['joints'])
 def test_invalid_dovetail_clearance_geometry(self):
  with self.assertRaises(ValueError):f.resolve(dict(dovetail_neck=10,dovetail_head=10))
if __name__=='__main__':unittest.main()
