"""CI helper: verify a CJK font is available for matplotlib."""
import sys
import matplotlib.font_manager as fm

available = {f.name for f in fm.fontManager.ttflist}
cjk_names = [
    'Microsoft YaHei', 'SimHei', 'SimSun', 'FangSong', 'KaiTi',
]
found = [n for n in cjk_names if n in available]

print(f"Total fonts registered: {len(available)}")
print(f"CJK fonts found: {found}")

if not found:
    print("WARNING: No CJK font found. Chinese labels may not render.")
    # Not a hard failure — DejaVu Sans fallback still works
else:
    print(f"OK: Will use '{found[0]}' for Chinese text rendering.")

sys.exit(0)
