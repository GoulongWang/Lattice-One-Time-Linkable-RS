import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

with open("benchmark_results.json") as f:
    data = json.load(f)
R = data["results"]
NS = [1, 8, 32]

def fmt_ms(x): return f"{x:.0f} ms" if x >= 10 else f"{x:.1f} ms"
def fmt_kb(x): return f"{x:.1f} KB"

rows = [
    ("KeyGen",       [fmt_ms(R[str(n)]["keygen_ms"]) for n in NS]),
    ("Sign",         [fmt_ms(R[str(n)]["sign_ms"])   for n in NS]),
    ("Verify",       [fmt_ms(R[str(n)]["verify_ms"]) for n in NS]),
    (None, None),
    ("PK",           [fmt_kb(R[str(n)]["pk_kb"])  for n in NS]),
    ("SK",           [fmt_kb(R[str(n)]["sk_kb"])  for n in NS]),
    ("Signature",    [fmt_kb(R[str(n)]["sig_kb"]) for n in NS]),
]

fig, ax = plt.subplots(figsize=(5.6, 3.4)); ax.axis("off")
table_data = [["Users"] + [str(n) for n in NS]]
for label, vals in rows:
    table_data.append(["", "", "", ""] if label is None else [label] + vals)

tbl = ax.table(cellText=table_data, cellLoc="center", loc="center")
tbl.auto_set_font_size(False); tbl.set_fontsize(13); tbl.scale(1, 1.95)
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor("black"); cell.set_linewidth(1.2)
    if r == 0:
        cell.set_text_props(fontweight="bold")
    if table_data[r][0] == "":          # separator
        cell.set_linewidth(0); cell.set_height(0.05)
fig.savefig("benchmark_table.png", dpi=220, bbox_inches="tight")

# markdown
md = ["| Users | " + " | ".join(str(n) for n in NS) + " |",
      "|---|" + "---|" * len(NS)]
md.append("| KeyGen | " + " | ".join(fmt_ms(R[str(n)]['keygen_ms']) for n in NS) + " |")
md.append("| Sign | "   + " | ".join(fmt_ms(R[str(n)]['sign_ms'])   for n in NS) + " |")
md.append("| Verify | " + " | ".join(fmt_ms(R[str(n)]['verify_ms']) for n in NS) + " |")
md.append("| PK | "  + " | ".join(fmt_kb(R[str(n)]['pk_kb'])  for n in NS) + " |")
md.append("| SK | "  + " | ".join(fmt_kb(R[str(n)]['sk_kb'])  for n in NS) + " |")
md.append("| Signature | " + " | ".join(fmt_kb(R[str(n)]['sig_kb']) for n in NS) + " |")
with open("benchmark_table.md", "w") as f:
    f.write("\n".join(md) + "\n")
print("\n".join(md))
print("\nenv:", data.get("env"))
print("wrote benchmark_table.png / benchmark_table.md")
