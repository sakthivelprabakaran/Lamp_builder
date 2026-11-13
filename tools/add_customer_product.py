"""Screen one reproducible product before adding it to the customer collection.
Usage: python3 tools/add_customer_product.py path/to/product.json
JSON fields: id, name, shape, structure, group, description, params.
"""
import sys,json,pathlib,re
from build_customer_catalog import ROOT,check

def publish():
 products=[]
 for p in (ROOT/'assets/customer/catalog').glob('*.json'):
  d=json.loads(p.read_text())
  if d.get('evidence',{}).get('geometry_passed'):products.append(d)
 # Spread silhouettes and structures across the opening gallery page.
 shapes=['Aster','Column','Cone','Flare','Urn','Pear','Hourglass','Barrel','Bell','Obelisk','Lantern','Tulip']
 textures=['Flow','Filigree','Canopy','Grove','Tide','Reed','Swell','Pleat','Spiral','Ripple']
 order={shape.lower()+'-'+textures[(r+i)%10].lower():r*12+i for r in range(10) for i,shape in enumerate(shapes)}
 featured=['aster-flow','column-pearl','cone-spiral','urn-dew','aster-botanical','column-pleat','urn-grove','pear-tide','hourglass-ripple','bell-swell','obelisk-reed','lantern-canopy','tulip-tide','barrel-grove','flare-pleat']
 products.sort(key=lambda d:(featured.index(d['id'])-100 if d['id'] in featured else order.get(d['id'],9999),d['name']))
 hashes=[d['evidence']['mesh_sha256'] for d in products]
 if len(set(hashes))!=len(hashes):raise ValueError('Duplicate mesh: review products before publication')
 result=dict(count=len(products),unique_meshes=len(set(hashes)),size_range_mm=[180,230],geometry_screen='upright A1 / 0.4 mm nozzle; geometric screening only; individual slicing and physical testing remain',designs=products)
 temp=ROOT/'assets/customer/catalog.tmp';temp.write_text(json.dumps(result,separators=(',',':')));temp.replace(ROOT/'assets/customer/catalog.json')
 return result
if __name__=='__main__':
 if len(sys.argv)>1:
  product=json.loads(pathlib.Path(sys.argv[1]).read_text())
  if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',product['id']):raise ValueError('Use a lowercase hyphenated id')
  product['thumbnail']='/assets/customer/catalog/'+product['id']+'.png'
  product['params']['support_free']=1
  check(product)
 data=publish();print('Published',data['count'],'individually geometry-screened products')
