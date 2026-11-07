# Active release: per-location data register

Generated with `uv run python scripts/generate_documentation.py`.

Release: `mcs-cbe101aec7584839`; format 2. This is a versioned snapshot.

The [JSON register](data-register.json) includes full source URLs/hashes, image IDs/hashes, review records, quiz IDs, action IDs and the exact file paths for every place.

## Coverage

| Place | Selected coordinate | Temperature months / years | Rainfall months / years | Historical / recent image |
|---|---|---|---|---|
| Dhaka / ঢাকা | 23.8103, 90.4125 | 540 / 45 | 0 / 0 | 1990-01-07 / 2025-02-08 |
| Chattogram / চট্টগ্রাম | 22.3569, 91.7832 | 540 / 45 | 0 / 0 | 1990-01-16 / 2025-01-16 |
| Khulna / খুলনা | 22.8456, 89.5403 | 540 / 45 | 0 / 0 | 1990-01-07 / 2025-02-08 |
| Rajshahi / রাজশাহী | 24.3745, 88.6042 | 540 / 45 | 0 / 0 | 1990-01-30 / 2025-01-14 |
| Sylhet / সিলেট | 24.8949, 91.8687 | 540 / 45 | 0 / 0 | 1990-01-16 / 2025-01-16 |
| Barishal / বরিশাল | 22.701, 90.3535 | 540 / 45 | 0 / 0 | 1990-01-07 / 2025-02-08 |
| Rangpur / রংপুর | 25.7439, 89.2752 | 540 / 45 | 0 / 0 | 1995-01-28 / 2025-01-14 |
| Mymensingh / ময়মনসিংহ | 24.7471, 90.4203 | 540 / 45 | 0 / 0 | 1990-01-07 / 2025-02-08 |
| Cox’s Bazar / কক্সবাজার | 21.4272, 92.0058 | 540 / 45 | 0 / 0 | 1990-01-16 / 2025-01-16 |
| Satkhira / সাতক্ষীরা | 22.7185, 89.0705 | 540 / 45 | 0 / 0 | 1990-01-30 / 2025-02-15 |
| Bhola / ভোলা | 22.6859, 90.6482 | 540 / 45 | 0 / 0 | 1990-01-07 / 2025-02-08 |
| Sunamganj / সুনামগঞ্জ | 25.0658, 91.395 | 540 / 45 | 0 / 0 | 1990-01-07 / 2025-02-08 |

## Exact resources

### Dhaka (`dhaka`)

- Story: `GET /api/v1/stories/dhaka?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/dhaka.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/dhaka.json`.
- Source SHA-256: `d44d265ad2f726327f7ffc2c0c7dbd0446c724196a36360a3dba0b4ed4ee5cb6`.
- Temperature series: `power-t2m-dhaka-a9370283a369e2bd-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-dhaka-cbe101ae`; state: `unavailable`.
- Shared-value annotations: none.
- Temperature review: `temperature-dhaka-0d444a984012`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_137044_19900107_20200916_02_T1_SR`; 1990-01-07; 667 × 667; valid coverage 99.5475%.
  Asset `/media/imagery/dhaka/before-06f95d647e5a.webp`; SHA-256 `06f95d647e5a0b4598a1b57d4525c6cb7fd1d190866b2a9d441b1e0cc47ce1ba`.
- After image: `LC08_L2SP_137044_20250208_20250214_02_T1_SR`; 2025-02-08; 667 × 667; valid coverage 99.6981%.
  Asset `/media/imagery/dhaka/after-8facb46b72b9.webp`; SHA-256 `8facb46b72b9dc5454de446911ab18b5ba3a98544187701f4aa341624731766d`.
- Quiz: `long-record`, `unit-reading`, `clouds`, `school-action`, `image-dhaka`.
- Actions: `river-story`, `water`, `school-shade`, `shade`.

### Chattogram (`chattogram`)

- Story: `GET /api/v1/stories/chattogram?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/chattogram.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/chattogram.json`.
- Source SHA-256: `7763425084d2a1d4d4964607d122a95e95c491266508f160bb8e9a68f272cd59`.
- Temperature series: `power-t2m-chattogram-07478e089dea083a-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-chattogram-cbe101ae`; state: `unavailable`.
- Shared-value annotations: none.
- Temperature review: `temperature-chattogram-5372a11ec7b8`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_136045_19900116_20200916_02_T1_SR`; 1990-01-16; 667 × 667; valid coverage 99.6556%.
  Asset `/media/imagery/chattogram/before-add49a3b30c1.webp`; SHA-256 `add49a3b30c19f473509d67fa33398c6698aeb70fe9d1f62b246b597343f036d`.
- After image: `LC08_L2SP_136045_20250116_20250127_02_T1_SR`; 2025-01-16; 667 × 667; valid coverage 99.5100%.
  Asset `/media/imagery/chattogram/after-9490846ba7a8.webp`; SHA-256 `9490846ba7a82475d62df163db1d3bb4011805548921f534ae3496c2cc18eb92`.
- Quiz: `anomaly`, `shared-values`, `image-date`, `school-action`, `image-chattogram`.
- Actions: `river-story`, `water`, `school-shade`, `shade`.

### Khulna (`khulna`)

- Story: `GET /api/v1/stories/khulna?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/khulna.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/khulna.json`.
- Source SHA-256: `54eba6738c3c542b3e7bc8261db63ba7169296a8c7352e54b53b15e16326e152`.
- Temperature series: `power-t2m-khulna-da268a914cb2fd77-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-khulna-cbe101ae`; state: `unavailable`.
- Shared-value annotations: none.
- Temperature review: `temperature-khulna-182d9d73b539`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_137044_19900107_20200916_02_T1_SR`; 1990-01-07; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/khulna/before-560c347e39f0.webp`; SHA-256 `560c347e39f0220e3a0f17f2f20704c03e1b5f1d27f23026b502f66b9804889d`.
- After image: `LC08_L2SP_137044_20250208_20250214_02_T1_SR`; 2025-02-08; 667 × 667; valid coverage 99.6932%.
  Asset `/media/imagery/khulna/after-e3b3375edf97.webp`; SHA-256 `e3b3375edf97f2709f6c50c675c1b1002c6d81cf37589e75d447564a3e1cd91b`.
- Quiz: `anomaly`, `baseline`, `clouds`, `heat-shade`, `image-khulna`.
- Actions: `river-story`, `water`, `school-shade`, `shade`.

### Rajshahi (`rajshahi`)

- Story: `GET /api/v1/stories/rajshahi?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/rajshahi.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/rajshahi.json`.
- Source SHA-256: `98e4856880162161003eaf0890320b31c0cc1648f2098b1c0ec5bc17ae472fe1`.
- Temperature series: `power-t2m-rajshahi-af9b970ee32b01c4-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-rajshahi-cbe101ae`; state: `unavailable`.
- Shared-value annotations: none.
- Temperature review: `temperature-rajshahi-0ae2deba60d3`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_138043_19900130_20200916_02_T1_SR`; 1990-01-30; 667 × 667; valid coverage 98.5217%.
  Asset `/media/imagery/rajshahi/before-099ff577fbd5.webp`; SHA-256 `099ff577fbd52c7e148befd5841685abb1d3b5b8faf4b5111d49fb51a6b478eb`.
- After image: `LC08_L2SP_138043_20250114_20250122_02_T1_SR`; 2025-01-14; 667 × 667; valid coverage 99.6559%.
  Asset `/media/imagery/rajshahi/after-a00a27684c8a.webp`; SHA-256 `a00a27684c8a56b68bd2afc3ea6026331e7dba2aab55498bcda5776c7caf6669`.
- Quiz: `anomaly`, `unit-reading`, `image-resolution`, `save-offline`, `image-rajshahi`.
- Actions: `river-story`, `field-calendar`, `school-shade`, `shade`.

### Sylhet (`sylhet`)

- Story: `GET /api/v1/stories/sylhet?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/sylhet.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/sylhet.json`.
- Source SHA-256: `5a095b2360691a6e5d7a476f53ec5d2d43d01690e97eaff93cfbe9a4f99f70bb`.
- Temperature series: `power-t2m-sylhet-eb2b38b4f432b3fb-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-sylhet-cbe101ae`; state: `unavailable`.
- Shared-value annotations: none.
- Temperature review: `temperature-sylhet-656afe9150da`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_136043_19900116_20200916_02_T1_SR`; 1990-01-16; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/sylhet/before-a6aded736cde.webp`; SHA-256 `a6aded736cdef694a099141c4b195074c7b49a125aa1ef48163b638649ece63a`.
- After image: `LC08_L2SP_136043_20250116_20250127_02_T1_SR`; 2025-01-16; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/sylhet/after-8c9e726c02e7.webp`; SHA-256 `8c9e726c02e746208fa879626ba0be4b0667e8c451c0152fb0102f220039689f`.
- Quiz: `rain-snow`, `shared-values`, `same-season`, `river-safety`, `image-sylhet`.
- Actions: `river-story`, `field-calendar`, `school-shade`, `shade`.

### Barishal (`barishal`)

- Story: `GET /api/v1/stories/barishal?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/barishal.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/barishal.json`.
- Source SHA-256: `c318bf5d64876d258d966c9f710f551122b7660d5687a88aea8a90fd1e83f856`.
- Temperature series: `power-t2m-barishal-e14c160c170912c5-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-barishal-cbe101ae`; state: `unavailable`.
- Shared-value annotations: bhola.
- Temperature review: `temperature-barishal-f764a70215e1`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_137044_19900107_20200916_02_T1_SR`; 1990-01-07; 667 × 667; valid coverage 99.6354%.
  Asset `/media/imagery/barishal/before-10dcbfdbe2fb.webp`; SHA-256 `10dcbfdbe2fb7a842a3c4daf9986013846dab5c8ca3e6b8cd532b65b8971bca0`.
- After image: `LC08_L2SP_137044_20250208_20250214_02_T1_SR`; 2025-02-08; 667 × 667; valid coverage 99.6446%.
  Asset `/media/imagery/barishal/after-76d59112e5c7.webp`; SHA-256 `76d59112e5c7b82ff1531b7b70f714657e97db19a552f5729aa7ce3467f021d1`.
- Quiz: `rain-snow`, `baseline`, `causation`, `heat-shade`, `image-barishal`.
- Actions: `river-story`, `field-calendar`, `school-shade`, `shade`.

### Rangpur (`rangpur`)

- Story: `GET /api/v1/stories/rangpur?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/rangpur.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/rangpur.json`.
- Source SHA-256: `54e4c81a38ec70d339ba4b11ab87df44b64d34c0ae0d30b4acc907df1f746bd0`.
- Temperature series: `power-t2m-rangpur-200485e9f40d1858-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-rangpur-cbe101ae`; state: `unavailable`.
- Shared-value annotations: none.
- Temperature review: `temperature-rangpur-f0f239e8d39a`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_138042_19950128_20200912_02_T1_SR`; 1995-01-28; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/rangpur/before-7ba33ddaaed4.webp`; SHA-256 `7ba33ddaaed4ed9b029a4e99dfe64b2e39dcf929acb158d9c599d8837931bfc1`.
- After image: `LC08_L2SP_138042_20250114_20250122_02_T1_SR`; 2025-01-14; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/rangpur/after-c995b7ae9a75.webp`; SHA-256 `c995b7ae9a75673ebe4fa9348f953b37fae7c1dde9f8cfb7bf5b40d9c480455b`.
- Quiz: `long-record`, `water-rate`, `vegetation-season`, `save-offline`, `image-rangpur`.
- Actions: `shade`, `field-calendar`, `school-shade`, `journal`.

### Mymensingh (`mymensingh`)

- Story: `GET /api/v1/stories/mymensingh?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/mymensingh.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/mymensingh.json`.
- Source SHA-256: `f52206195bdf6fe58d4d20a4beae03c65d18b8b331c24674a30e20c6a5de7d02`.
- Temperature series: `power-t2m-mymensingh-41cb53f8ba872d25-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-mymensingh-cbe101ae`; state: `unavailable`.
- Shared-value annotations: none.
- Temperature review: `temperature-mymensingh-a0ee64dc45da`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_137043_19900107_20200916_02_T1_SR`; 1990-01-07; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/mymensingh/before-071754f76a8a.webp`; SHA-256 `071754f76a8aaca98a9ee815a699fb5717e165a89d210978d6b3c5e357ba92f6`.
- After image: `LC08_L2SP_137043_20250208_20250214_02_T1_SR`; 2025-02-08; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/mymensingh/after-47ed2cd5005a.webp`; SHA-256 `47ed2cd5005a076f1a3b2fdfe66285acbb5b7f6334d44047168c54554332c1ca`.
- Quiz: `anomaly`, `water-rate`, `causation`, `school-action`, `image-mymensingh`.
- Actions: `river-story`, `field-calendar`, `school-shade`, `shade`.

### Cox’s Bazar (`coxs_bazar`)

- Story: `GET /api/v1/stories/coxs_bazar?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/coxs_bazar.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/coxs_bazar.json`.
- Source SHA-256: `ec9943bebdbdddfef7581f75a44f7bd276781259639c1039ae4d46daf3f107da`.
- Temperature series: `power-t2m-coxs_bazar-392941e5ca7c54c1-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-coxs_bazar-cbe101ae`; state: `unavailable`.
- Shared-value annotations: none.
- Temperature review: `temperature-coxs_bazar-9843f0a0b404`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_136045_19900116_20200916_02_T1_SR`; 1990-01-16; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/coxs_bazar/before-256f7c3328f5.webp`; SHA-256 `256f7c3328f5bfce5e5585fc23d6f1598277d96ede26a69d54ce8fce9a927b4c`.
- After image: `LC08_L2SP_136045_20250116_20250127_02_T1_SR`; 2025-01-16; 667 × 667; valid coverage 99.7001%.
  Asset `/media/imagery/coxs_bazar/after-35db107eeccd.webp`; SHA-256 `35db107eeccdeb4951b1414ddad07c3a8eff0ca88d56d0fa2878b85f7b252e4a`.
- Quiz: `equal-decade`, `global-local`, `image-resolution`, `save-offline`, `image-coxs_bazar`.
- Actions: `river-story`, `water`, `school-shade`, `shade`.

### Satkhira (`satkhira`)

- Story: `GET /api/v1/stories/satkhira?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/satkhira.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/satkhira.json`.
- Source SHA-256: `7409190a8cdb4c5d44a69712ce0fb71a41c8da40bcd59d7df343011135ff7fd6`.
- Temperature series: `power-t2m-satkhira-9671072aa2e28323-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-satkhira-cbe101ae`; state: `unavailable`.
- Shared-value annotations: none.
- Temperature review: `temperature-satkhira-d5376cb4ca0c`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_138044_19900130_20200916_02_T1_SR`; 1990-01-30; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/satkhira/before-e627bee47395.webp`; SHA-256 `e627bee47395a48b83713a6181b2514d7ba6035866a87edd3de8f3dc63c7c2e9`.
- After image: `LC08_L2SP_138044_20250215_20250226_02_T1_SR`; 2025-02-15; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/satkhira/after-2a0807809853.webp`; SHA-256 `2a080780985387d9f561e7b6533ce56bebe50bb73b65a54fb1aa801d51d49a43`.
- Quiz: `weather-climate`, `source-check`, `image-resolution`, `school-action`, `image-satkhira`.
- Actions: `shade`, `field-calendar`, `school-shade`, `journal`.

### Bhola (`bhola`)

- Story: `GET /api/v1/stories/bhola?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/bhola.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/bhola.json`.
- Source SHA-256: `17449929bd75462186ce7449c991dec4dd4078a381ff055dd45d1a66d3827aff`.
- Temperature series: `power-t2m-bhola-e14c160c170912c5-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-bhola-cbe101ae`; state: `unavailable`.
- Shared-value annotations: barishal.
- Temperature review: `temperature-bhola-f764a70215e1`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_137044_19900107_20200916_02_T1_SR`; 1990-01-07; 667 × 667; valid coverage 99.5046%.
  Asset `/media/imagery/bhola/before-4c44036a04a5.webp`; SHA-256 `4c44036a04a5145efa17cf7b7aed0d475f3fc341dfd0a819685bbfc91a719775`.
- After image: `LC08_L2SP_137044_20250208_20250214_02_T1_SR`; 2025-02-08; 667 × 667; valid coverage 99.6435%.
  Asset `/media/imagery/bhola/after-7819fe0cba0c.webp`; SHA-256 `7819fe0cba0cb11ef0126f11cdbd878c8865fa17c99406f1e19442eefc32af05`.
- Quiz: `anomaly`, `water-rate`, `image-resolution`, `heat-shade`, `image-bhola`.
- Actions: `river-story`, `field-calendar`, `save-energy`, `journal`.

### Sunamganj (`sunamganj`)

- Story: `GET /api/v1/stories/sunamganj?release=mcs-cbe101aec7584839`.
- POWER input: `data/raw/power/sunamganj.json`; pinned evidence: `data/processed/releases/mcs-cbe101aec7584839/inputs/power/sunamganj.json`.
- Source SHA-256: `8ca93ca616b158f19a1b4da2aa40dbba57766c15be36c35408ae5fb0f0b718ae`.
- Temperature series: `power-t2m-sunamganj-fe4ed3964be1d2a4-cbe101ae`; state: `comparison_approved`.
- Rainfall series: `imerg-pending-sunamganj-cbe101ae`; state: `unavailable`.
- Shared-value annotations: none.
- Temperature review: `temperature-sunamganj-f906272d293c`; windows 2001–2010 and 2016–2025.
- Before image: `LT05_L2SP_137043_19900107_20200916_02_T1_SR`; 1990-01-07; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/sunamganj/before-21ef2657f578.webp`; SHA-256 `21ef2657f5787025fcc2d09caf92bbd55ac2aecb97086db46066cf5b0f3d4af7`.
- After image: `LC08_L2SP_137043_20250208_20250214_02_T1_SR`; 2025-02-08; 667 × 667; valid coverage 99.7004%.
  Asset `/media/imagery/sunamganj/after-2c1c0a607c12.webp`; SHA-256 `2c1c0a607c1215ebc7fcd7a3be3e841cc12beb2c1929ac453631a2943a4d871f`.
- Quiz: `observation`, `global-local`, `clouds`, `river-safety`, `image-sunamganj`.
- Actions: `river-story`, `field-calendar`, `save-energy`, `journal`.
