"""A1 geometry regressions; run python3 -m unittest test_print_geometry."""
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import lamp_engine as engine
import print_geometry
import server

ROOT = pathlib.Path(__file__).parent

class ManufacturingTests(unittest.TestCase):
    def test_presets_are_closed_connected_upright_and_pass_overhang_screen(self):
        for path in (ROOT / 'presets').glob('*.json'):
            with self.subTest(preset=path.name):
                p=json.loads(path.read_text())['shade']
                v,f=engine.build_shade_mesh(p)
                ok,report=engine.verify_mesh(v,f)
                self.assertTrue(ok,report)
                self.assertEqual(float(v[:,2].min()),0.)
                self.assertTrue(print_geometry.manufacturing_report(v,f)['passed'])

    def test_graph_weave_keeps_topology_at_preview_and_export_resolution(self):
        p=json.loads((ROOT/'presets/Showcase - Rattan Relief.json').read_text())['shade']
        topology=[]
        for nt,nz in ((160,120),(560,320)):
            v,f=engine.build_shade_mesh(dict(p,res_theta=nt,res_z=nz))
            ok,r=engine.verify_mesh(v,f)
            self.assertTrue(ok,r)
            self.assertEqual(r['components'],1)
            topology.append(r['euler'])
        self.assertEqual(topology[0],topology[1])

    def test_degenerate_closed_mesh_is_rejected(self):
        v=np.zeros((4,3));f=np.array([[0,2,1],[0,1,3],[1,2,3],[2,0,3]])
        ok,r=engine.verify_mesh(v,f)
        self.assertFalse(ok)
        self.assertEqual(r['degenerate_triangles'],4)

    def test_woven_feature_measurements_exceed_minimums(self):
        p=json.loads((ROOT/'presets/Woven Rattan Gourd.json').read_text())['shade']
        v,f=engine.build_shade_mesh(p)
        m=print_geometry.measure_features(v,f,18.)
        self.assertGreaterEqual(m['minimum_aperture_clearance_mm'],1.6)
        self.assertGreaterEqual(m['minimum_normal_wall_estimate_mm'],.8)
        self.assertEqual(m['aperture_count'],144)

    def test_invalid_dimensions_are_rejected(self):
        for p in ({'height':260},{'wall':.4},{'r_bottom':180,'r_top':180}):
            with self.subTest(params=p),self.assertRaises(ValueError):
                engine.build_shade_mesh(p)

    def test_export_failure_never_writes_an_stl(self):
        with patch.object(engine,'verify_mesh',return_value=(False,{'valid':False})), \
             patch.object(engine,'write_binary_stl') as write:
            result=server.make_shade({},preview=False,export=True)
            self.assertFalse(result['ok'])
            write.assert_not_called()
        with patch.object(print_geometry,'manufacturing_report',return_value={
                'passed':False,'errors':['unsupported roof']}), \
             patch.object(engine,'write_binary_stl') as write:
            result=server.make_shade({},preview=False,export=True)
            self.assertFalse(result['ok'])
            write.assert_not_called()

    def test_export_passes_and_matches_preview_contours(self):
        p=json.loads((ROOT/'presets/Woven Rattan Gourd.json').read_text())['shade']
        with tempfile.TemporaryDirectory() as directory,patch.object(server,'OUTDIR',directory):
            preview=server.make_shade(p,preview=True)
            result=server.make_shade(p,preview=False,export=True)
            self.assertTrue(result['ok'],result)
            self.assertTrue(result['manufacturing']['passed'])
            self.assertEqual(result['metrics']['tris'],preview['metrics']['tris'])
            self.assertTrue((pathlib.Path(directory)/'shade.stl').is_file())

if __name__=='__main__':unittest.main()
