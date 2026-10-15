#!/usr/bin/env bash
# Install the HP DesignJet T130 driver (hpcups + t130wrap) and create a CUPS queue.
#
# Usage: sudo bash install.sh PRINTER_IP [QUEUE_NAME]
#   PRINTER_IP   IP or hostname of the T130 (raw port 9100 must be reachable)
#   QUEUE_NAME   defaults to DesignJet-T130
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Run as root: sudo $0 PRINTER_IP [QUEUE_NAME]" >&2
    exit 1
fi
if [[ $# -lt 1 ]]; then
    echo "Usage: sudo $0 PRINTER_IP [QUEUE_NAME]" >&2
    exit 1
fi

IP="$1"
QUEUE="${2:-DesignJet-T130}"
HERE="$(cd "$(dirname "$0")" && pwd)"

# The cups filter directory varies by distro; ask CUPS where it is.
FILTER_DIR="$(cups-config --serverbin 2>/dev/null || echo /usr/lib/cups)/filter"

for dep in python3 lpadmin; do
    command -v "$dep" >/dev/null || { echo "Missing dependency: $dep" >&2; exit 1; }
done
if [[ ! -x "$FILTER_DIR/hpcups" ]]; then
    echo "hpcups not found in $FILTER_DIR. Install HPLIP first:" >&2
    echo "  Arch:          pacman -S hplip" >&2
    echo "  Debian/Ubuntu: apt install printer-driver-hpcups" >&2
    echo "  Fedora:        dnf install hplip" >&2
    exit 1
fi

install -m 0755 "$HERE/t130wrap" "$FILTER_DIR/t130wrap"
echo "Installed filter: $FILTER_DIR/t130wrap"

lpadmin -p "$QUEUE" -E \
    -v "socket://$IP:9100" \
    -P "$HERE/hp-designjet-t130.ppd" \
    -D "HP DesignJet T130 24-in" 2>&1 | grep -v "deprecated" || true
cupsenable "$QUEUE" 2>/dev/null || true
cupsaccept "$QUEUE" 2>/dev/null || true

echo "Queue '$QUEUE' -> socket://$IP:9100"
echo "Test: lp -d $QUEUE -o media=Letter <file.pdf>"
