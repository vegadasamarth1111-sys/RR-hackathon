import os
import win32com.client

base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
pptx = os.path.join(base, "outputs", "SupeRR_Selector_Deck.pptx")
out = os.path.join(base, "analysis", "deck_preview")
os.makedirs(out, exist_ok=True)
app = win32com.client.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(pptx, WithWindow=False)
for i, slide in enumerate(pres.Slides, start=1):
    slide.Export(os.path.join(out, f"slide{i:02d}.png"), "PNG", 1600, 900)
pres.Close()
app.Quit()
print("exported", i)
