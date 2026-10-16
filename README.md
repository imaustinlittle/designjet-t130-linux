# designjet-t130-linux

A working Linux driver for the **HP DesignJet T130 24-in** large-format printer.

HP ships T130 drivers for Windows and macOS only, and HPLIP has never listed the
T1xx/T5xx DesignJets. Driverless printing (IPP Everywhere / PCLm) is accepted by
the printer but rejected at the content level (`document-format-error`). This
project gets you native, full-quality printing from any Linux app with a normal
print dialog.

## How it works

The T130 speaks **PCL3GUI** with **Mode 10** compressed RGB raster, the same
format HPLIP's `hpcups` filter already generates for 50+ HP inkjets through its
`pcl3gui2` encoder. Captures of HP's Windows driver matched that encoder almost
byte for byte. So this driver is:

- **`hp-designjet-t130.ppd`**: a PPD that selects hpcups' `pcl3gui2` encoder and
  describes the T130's paper sizes, margins, quality modes and media types.
- **`t130wrap`**: a small CUPS filter that runs hpcups and fixes the two places
  where its output differs from what the T130 accepts.

No HP code is included or required. See [docs/protocol.md](docs/protocol.md) for
the full analysis.

## Features

| Feature | Status |
|---|---|
| Color printing | Working, colors verified |
| Print quality Normal / Best | Working |
| Maximum detail (1200 dpi output, photo paper) | Working, same commands as Windows |
| Sizes Letter, Legal, Tabloid, A4 to A1, Arch C/D, ANSI C/D | Working |
| 24x36 (Arch D) poster on 24 in roll | Verified on hardware |
| Custom sizes up to 24 in wide | Working |
| Media type: printer settings, photo paper | Working |
| Grayscale mode | Not yet |
| Paper source: auto-select | Verified on sheets and roll |
| Paper source: roll (explicit) | Added in 0.4.0, not yet tested on hardware |
| Roll cutting | Verified: the printer cuts at the end of each roll job |
| Other media types | Not yet |

Tested with HPLIP 3.23 and 3.26, cups-filters 2.0, CUPS 2.4.

## Requirements

- CUPS
- HPLIP's `hpcups` filter
  - Arch: `pacman -S hplip`
  - Debian/Ubuntu: `apt install printer-driver-hpcups`
  - Fedora: `dnf install hplip`
- Python 3
- Network access to the printer on TCP 9100 (raw printing)

## Install

```sh
git clone https://github.com/imaustinlittle/designjet-t130-linux.git
cd designjet-t130-linux
sudo bash install.sh 192.0.2.50          # your printer's IP or hostname
lp -d DesignJet-T130 -o media=Letter some.pdf
```

The queue then shows up in every app's print dialog. To pick quality and media:

```sh
lp -d DesignJet-T130 -o media=ARCHD -o OutputMode=Best poster.pdf
lp -d DesignJet-T130 -o MediaType=Photo -o OutputMode=MaxDetail photo.pdf
lp -d DesignJet-T130 -o media=ARCHD -o InputSlot=Roll -o fit-to-page poster.png
```

The printer cannot print within about 5 mm of the edges, so use `fit-to-page`
for artwork made at exactly the paper size. Roll jobs are cut by the printer
itself; the driver sends no cut command (neither does HP's Windows driver).
If roll prints come out uncut, check the cutter setting on the front panel.

CUPS prints a "printer drivers are deprecated" warning when a PPD is used. It is
harmless on CUPS 2.4.

## Troubleshooting

- **Blank page:** check `journalctl -u cups | grep t130wrap`. The filter logs how
  many commands it patched. If the PDF came from an unusual generator, look for
  `pdftopdf` errors; rewriting it with
  `gs -o fixed.pdf -sDEVICE=pdfwrite input.pdf` helps.
- **"File is for 11 inch" prompt on the printer:** the job is wider than the
  loaded paper. Portrait sizes on sheets avoid this.

## Firmware note

The printer phones home for firmware updates. Newer HP firmware has been known to
reject third-party ink. If that matters to you, turn off automatic updates in the
printer's web interface and consider blocking its internet access at your
firewall.

## Contributing

Captures from other T1xx/T5xx models (T100, T120, T125, T520, T525, T530) would
help extend this. [docs/protocol.md](docs/protocol.md) describes the capture
method, and `tools/pcltok.py` decodes captures.

## License

MIT. See [LICENSE](LICENSE). HP and DesignJet are trademarks of HP Inc. This
project is not affiliated with or endorsed by HP.
