# Lume product library

The customer preview is `/customer`, alongside the internal studio at `/`.
The library combines twelve designed silhouettes with ten structure treatments:
Flow, Filigree and Canopy woven ribs; Grove organic openings; Tide graded wave
lattice; Pleat, Reed, Swell, Spiral and Ripple continuous walls. These are
reproducible studio parameters, not color copies or preloaded full meshes.
All perforated products currently use the engine's support-aware pointed
opening construction. The continuous-wall products use the studio's flute,
twist and ripple operators. They do not share a perforation template.

`assets/customer/catalog.json` is the index. Each product also has its own JSON
and actual-mesh PNG in `assets/customer/catalog/`. The gallery searches names
and structures, filters silhouette or family, and paginates twelve designs.
Only the selected design requests a full mesh; images load lazily.

## Validation states

- Candidate: saved settings awaiting the checks below; excluded from the index.
- Geometry screened: closed, connected, nondegenerate mesh with consistent winding;
  A1 envelope and upright facet-overhang screen; estimated wall and aperture-web
  measurements. Four height/density corner cases pass the facet screen. This is
  geometric evidence, not a slicer or physical print guarantee.
- Individually sliced: the exact saved default model has its own Bambu result,
  supports off, provisional Generic PLA. Modified size or density returns to
  geometry-screened status. Slicing does not establish physical success.
- Physically tested: record the product/settings hash, material, profile, result,
  photographs and any defects after the owner actually prints it. No library
  product currently has this status. Owner aesthetic acceptance is separate.

All exports still pass the server's mesh, overhang and feature gate. A successful
preview alone does not bypass export validation. Feature projection is an
estimate and does not replace full self-intersection or medial-axis analysis.

## Add a product one at a time

1. Tune a design in the internal studio and save its preset. Visually review its
   proportions and structure. Copy its `shade` settings into `params` in a new
   product JSON with `id`, `name`, `shape`, `structure`, `group`, and `description`.
   Use a lowercase hyphenated id and group Woven, Organic, Lattice or Solid.
   Keep a draft outside `assets/customer/catalog/` until checked.
2. Run `python3 tools/add_customer_product.py path/to/product.json`. It builds
   the real mesh, gates geometry, measures features, renders its thumbnail and
   checks the supported customization corners before indexing it. It refuses
   duplicate mesh hashes. Review the actual thumbnail and hero before accepting
   the aesthetics. Neither the count nor the geometric gate grants aesthetic
   acceptance. The tool currently supports the flat studio controls; graph-based
   products need their own explicit customization mapping before addition.
3. Export that exact model, then run
   `python3 tools/slice_a1.py path/to/product.stl --output output/revamp/products/product-id`.
   Keep the slicer evidence associated with this id and exact parameters.
4. Print and inspect it individually, then record material, profile and findings.
   Do not transfer one product's slicer or physical result to another product.

`tools/build_customer_catalog.py` regenerates the initial parameter library and
screens each result individually. `tools/add_customer_product.py` without an
argument rebuilds the index from passing per-product records. Running the bulk
builder replaces generated records, so keep owner test/acceptance records in a
separate review log and re-associate them only when the mesh hash matches.

The catalog is a local design preview collection, not a deployed shop or a claim
that 120 designs have been owner approved. The original approved woven print
review is documented separately in PRINTING.md.
