# HP DesignJet T130 print protocol notes

How the T130's job format was worked out, what it contains, and how it maps onto
HPLIP's existing `pcl3gui2` encoder.

## Summary

- Job language: **PJL wrapper + PCL3GUI**.
- Raster: **Mode 10** compression, 24-bit RGB, **600 x 600 ppi** in every mode.
- The structure matches HPLIP's `prnt/hpcups/Pcl3Gui2.cpp`. Two fixes make
  hpcups output acceptable to the T130:
  1. Configure Raster Data byte 2: `0x07` (hpcups) becomes `0x1F` (Windows).
  2. Remove `ESC &l-2H` (media preload). With it, the printer feeds the sheet
     out blank.

## What did not work

- **IPP Everywhere / driverless:** the printer advertises
  `application/vnd.hp-PCL`, `image/jpeg`, `application/PCLm` and
  `application/octet-stream`. No PWG raster or PDF, so `-m everywhere` fails.
- **PCLm via cups-filters:** generated PCLm matched every advertised parameter
  (600 dpi, strip height 32, RLE) and was still rejected with
  `client-error-document-format-error` when sent with the exact advertised MIME
  type. The firmware does not accept Ghostscript's PCLm.
- **JPEG** prints fine and is a usable fallback, but loses print dialogs and
  quality modes.
- **HPLIP model list:** the `HP DesignJet 130` entries in foomatic are a 2004
  printer of the same name, not the T130.

## Capture method

1. Download the T130 V4 driver from the Microsoft Update Catalog (search
   "DesignJet T130", HP Printer 61.2509.0.100). The `.cab` contains
   `hpi2144.inf`. HP's `IntegratedInstaller.exe` is only a bootstrapper that
   downloads the driver at install time.
2. Windows x64 VM with **no network** (Windows on ARM cannot load the x64 print
   driver). Files moved in and out on an MBR-partitioned exFAT disk image
   attached over USB; an unpartitioned image shows as unallocated in Windows.
3. Install the driver on the `FILE:` port, print test pages, save `.prn` files.
4. Change one setting per capture to isolate which bytes encode it.

The PJL header of a capture contains the Windows hostname, username, a job GUID
and CPU model. Sanitize before sharing captures.

## Job structure (Windows driver 61.2509, Letter, Normal)

```
<18000 x 0x00>                       padding, not required
ESC E
ESC %-12345X @PJL JOB
@PJL SET STRINGCODESET = UTF8
@PJL SET JOBATTR = "JobAcct..."      job accounting, not required
@PJL SET JOBNAME = "..."
@PJL SET RENDERINTENT = PERCEPTUAL
@PJL ENTER LANGUAGE = PCL3GUI
ESC E
ESC &l7H                             paper source (7 = auto-select)
ESC &l-1M                            media type (-1 = use printer settings)
ESC *o5W 0D 03 00 07 CF              media subtype
ESC *o5W 0B 01 00 00 00              grayscale flag (00 = color)
ESC *o5W 0E 03 00 00 00              unknown, always 0 in captures
ESC &u600D                           unit of measure
ESC *o0M                             print mode
ESC *o5W 0D 02 00 00 0x              page-content flag (varies per page; not cut)
ESC *g12W 06 1F 00 01 02 58 02 58 0A 01 20 01   Configure Raster Data
ESC *r6364S                          raster width in pixels
ESC &l101A                           paper size 101 = custom
ESC *o5W 0E 05 00 19 C8              custom width,  600 dpi units (6600 = 11 in)
ESC *o5W 0E 06 00 13 EC              custom height, 600 dpi units (5100 = 8.5 in)
ESC *r1A                             start raster
ESC *b#W <Mode 10 row> ...           one per row; 0-length = repeat seed row
ESC *rC                              end raster
0x0C  ESC E  ESC %-12345X @PJL EOJ
```

### Configure Raster Data

```
06        format
1F        special purpose byte (hpcups color-only mode sends 07)
00 01     one component
02 58     horizontal resolution 600
02 58     vertical resolution 600
0A        compression mode 10
01        orientation
20        bits per pixel field
01        planes
```

### Settings observed

| Setting | `*o#M` | `&l#M` | Subtype (`*o5W 0D 03`) |
|---|---|---|---|
| Normal, printer settings | 0 | -1 | `07 CF` (1999) |
| Best, printer settings | 1 | -1 | `07 CF` |
| Best, photo paper | 1 | 3 | `06 AF` (1711) |
| Maximum detail, photo paper | 2 | 3 | `06 AF` |

Maximum detail does **not** send 1200 ppi data. The CRD stays 600 x 600; print
mode 2 tells the printer to place dots at 1200 dpi from 600 ppi input. The
Windows driver only enables it with a photo media type.

Paper source `&l15H` appeared when roll was selected explicitly; `7` is
auto-select and works for both sheets and roll. The PPD exposes both
(`InputSlot=Auto`, `InputSlot=Roll`, MediaPosition 7 and 15).

No cut command appears in any capture, roll jobs included. Cutting is a
printer-side setting. `*o5W 0D 02` differs between roll captures but also
varies on sheet jobs, so it is a page-content flag, not a cut flag.

The Windows driver lays Letter out landscape (11 in across the 24 in roll).
hpcups lays it out portrait, which is correct for sheets. Both print.

## Mapping to hpcups

hpcups reads job settings from the CUPS raster header, which the PPD controls:

| PCL | Source in PPD |
|---|---|
| `&l#H` | `MediaPosition` (InputSlot) |
| `&l#M` | `cupsMediaType` (MediaType) |
| `&l#A` | `cupsInteger0` (101 for all sizes, so hpcups sends `0E 05/06`) |
| `*o5W 0D 03` subtype | `cupsInteger6` |
| `*o#M` | `OutputType` (OutputMode) |
| CRD resolution | `HWResolution` |
| `hpPrinterLanguage: "pcl3gui2"` | selects the `Pcl3Gui2` encapsulator |

Differences remaining between hpcups and Windows output, all accepted by the
printer: hpcups also sends `*t600R`, positions with `*p#Y` and skips blank
rows with `*b#Y`, omits the `0B 01`, `0E 03` and `0D 02` configuration
commands, and does not send the leading null padding.

## Bisection that found the preload problem

Each file sent raw (`lp -o raw`) to a T130 with Letter sheets loaded:

| Test | Result |
|---|---|
| Windows capture replayed (landscape, roll layout) | Blank, size mismatch prompt |
| hpcups output minus `&l-2H` | Printed correctly |
| plus `*p#Y` / `*b#Y` expanded to blank rows, `ESC E` added | Printed correctly |
| plus landscape layout | Printed, offset, size mismatch prompt |

## Tools

- `tools/pcltok.py FILE [N]` tokenizes a PCL capture and prints commands with
  payload previews.
- `tools/gen_testpages.py DIR` writes the test pages used for captures.
