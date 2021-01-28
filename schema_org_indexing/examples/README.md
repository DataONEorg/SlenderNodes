# Example Schema.org JSON-LD

## Reliable examples

### BCO-DMO Sources

A couple of items randomly selected from [BCO-DMO Datasets](https://www.bco-dmo.org/search/dataset)

- eg_bcodmo_01
  - Source: https://www.bco-dmo.org/dataset/826798
  - JSON-LD: [eg_bcodmo_01.jsonld](eg_01.jsonld)
  - JSON-LD [Playground](https://json-ld.org/playground/#startTab=tab-expanded&json-ld=https%3A%2F%2Fraw.githubusercontent.com%2FDataONEorg%2FSlenderNodes%2Fschema-org-indexing%2Fschema_org_indexing%2Fexamples%2Feg_bcodmo_01.jsonld)
- eg_bcodmo_02
  - Source: https://www.bco-dmo.org/dataset/835593
  - JSON-LD: [eg_bcodmo_02.jsonld](eg_02.jsonld)
  - JSON-LD [Playground](https://json-ld.org/playground/#startTab=tab-expanded&json-ld=https%3A%2F%2Fraw.githubusercontent.com%2FDataONEorg%2FSlenderNodes%2Fschema-org-indexing%2Fschema_org_indexing%2Fexamples%2Feg_bcodmo_02.jsonld)
- eg_bcodmo_01-hacked This copy of eg_bcodmo_01 has been modified to set the `@container` for `creator` to `@list` to preserve ordering.
  - Source: https://www.bco-dmo.org/dataset/826798
  - JSON-LD: [eg_bcodmo_01-hacked.jsonld](eg_01.jsonld)
  - JSON-LD [Playground](https://json-ld.org/playground/#startTab=tab-expanded&json-ld=https%3A%2F%2Fraw.githubusercontent.com%2FDataONEorg%2FSlenderNodes%2Fschema-org-indexing%2Fschema_org_indexing%2Fexamples%2Feg_bcodmo_01-hacked.jsonld)

### Dryad Sources

- eg_dryad_01
  - Source: https://datadryad.org/stash/dataset/doi:10.5061/dryad.g79cnp5ng
  - JSON-LD: [eg_dryad_01.jsonld](eg_dryad_01.jsonld)
  - JSON-LD [Playground](https://json-ld.org/playground/#startTab=tab-expanded&json-ld=https%3A%2F%2Fraw.githubusercontent.com%2FDataONEorg%2FSlenderNodes%2Fschema-org-indexing%2Fschema_org_indexing%2Fexamples%2Feg_dryad_01.jsonld)

- eg_dryad_02
  - Source: http://datadryad.org/stash/dataset/doi:10.5061/dryad.nm13s
  - JSON-LD: [eg_dryad_02.jsonld](eg_dryad_02.jsonld)
  - JSON-LD [Playground](https://json-ld.org/playground/#startTab=tab-expanded&json-ld=https%3A%2F%2Fraw.githubusercontent.com%2FDataONEorg%2FSlenderNodes%2Fschema-org-indexing%2Fschema_org_indexing%2Fexamples%2Feg_dryad_02.jsonld)

### PANGAEA Sources

- eg_pangaea_01
  - Source: https://doi.pangaea.de/10.1594/PANGAEA.925562
  - JSON-LD: [eg_pangaea_01.jsonld](eg_pangaea_01.jsonld)
  - JSON-LD [Playground](https://json-ld.org/playground/#startTab=tab-expanded&json-ld=https%3A%2F%2Fraw.githubusercontent.com%2FDataONEorg%2FSlenderNodes%2Fschema-org-indexing%2Fschema_org_indexing%2Fexamples%2Feg_pangaea_01.jsonld)

## Examples currently requiring a name space correction hack

In each case below, the sources provide an incorrect name space for `SO` content. The example JSON-LD documents have been normalized to a name space of 
`https://schema.org/`.

### Hydroshare

Currently uses a `SO` name space of `http://www.schema.org/`.

- eg_hydroshare_01
  - Source: https://www.hydroshare.org/resource/d5ba5d65348f4c4088bc0e4d1b9c8291/
  - JSON-LD: [eg_hydroshare_01.jsonld](eg_hydroshare_01.jsonld)
  - JSON-LD [Playground](https://json-ld.org/playground/#startTab=tab-expanded&json-ld=https%3A%2F%2Fraw.githubusercontent.com%2FDataONEorg%2FSlenderNodes%2Fschema-org-indexing%2Fschema_org_indexing%2Fexamples%2Feg_hydroshare_01.jsonld)

### EarthChem

Currently uses a `SO` namespace of `http://schema.org`.

- eg_earthchem_01
  - Source: https://ecl.earthchem.org/view.php?id=1777
  - JSON-LD: [eg_earthchem_01.jsonld](eg_earthchem_01.jsonld)
  - JSON-LD [Playground](https://json-ld.org/playground/#startTab=tab-expanded&json-ld=https%3A%2F%2Fraw.githubusercontent.com%2FDataONEorg%2FSlenderNodes%2Fschema-org-indexing%2Fschema_org_indexing%2Fexamples%2Feg_earthchem_01.jsonld)

