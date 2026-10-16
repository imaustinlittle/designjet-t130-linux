# Changelog

## 0.4.0 (2026-10-16)
- Add `InputSlot=Roll` (`ESC &l15H`), as the Windows driver sends for roll jobs. Auto-select stays the default.
- Document that roll cutting is done by the printer, not the driver.
- Verified on hardware: 24x36 poster printed from a 24 in roll (driver 0.3.0, auto-select) and cut cleanly at the end of the job.

## 0.3.0 (2026-10-15)
- Strip hpcups' media preload (`ESC &l-2H`), which made the T130 feed pages out blank.
- First version verified on hardware: black and color test pages print correctly.

## 0.2.0
- Add Best and Maximum detail print modes and a Photo paper media type.
- Maximum detail limited to photo paper, as in HP's Windows driver.

## 0.1.0
- Initial PPD using hpcups `pcl3gui2`, plus `t130wrap` CRD patch.
