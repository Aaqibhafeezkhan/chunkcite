"""Render assets/demo.gif from the actual CLI outputs captured in this repo.

Frames are the literal terminal text from:
  chunkcite chunk examples/docs/rag-guide.md
  chunkcite eval --chunks chunks.jsonl --golden examples/golden.jsonl
  chunkcite verify --chunks chunks.jsonl --claims examples/claims.json
No numbers are invented here; edit a frame and the GIF changes with it.
"""

from PIL import Image, ImageDraw, ImageFont

FRAMES = [
    "$ chunkcite chunk examples/docs/rag-guide.md\n5 chunks\n"
    "d25a82cbe8e6  [Chunking]  Split documents at headings,\n"
    "               never mid-sentence.\n"
    "5317ae3b980c  [Tables]    | retriever | strength |\n"
    "               | BM25 | exact terms, dates, names |",
    "$ chunkcite eval --chunks chunks.jsonl --golden examples/golden.jsonl\n"
    '{\n  "cases": 4,\n  "k": 5,\n  "recall@5": 1.0,\n  "mrr": 1.0\n}',
    "$ chunkcite verify --chunks chunks.jsonl --claims examples/claims.json\n"
    "2/3 claims supported\n"
    "supported   Split documents at headings, never mid-sentence.\n"
    "supported   pgvector adds vector similarity search to Postgres...\n"
    "unsupported pgvector is 99 percent faster...  (overlap 0.125)",
]

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
except OSError:
    font = ImageFont.load_default()

images = []
for text in FRAMES:
    img = Image.new("RGB", (820, 220), (16, 20, 24))
    draw = ImageDraw.Draw(img)
    draw.multiline_text((16, 16), text, fill=(220, 230, 220), font=font, spacing=6)
    images.append(img)

images[0].save(
    "assets/demo.gif", save_all=True, append_images=images[1:],
    duration=2200, loop=0,
)
print("wrote assets/demo.gif")
