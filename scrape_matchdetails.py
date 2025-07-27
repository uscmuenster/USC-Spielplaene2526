import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Ziel-URL
url = "https://www.volleyball-bundesliga.de/popup/matchSeries/matchDetails.xhtml?matchId=771119420"

# HTML laden
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

# Extrahiere alle relevanten Textinformationen
text_parts = []
for element in soup.select("body *"):
    if element.name in ["p", "h1", "h2", "h3", "table", "tr", "td", "th", "span", "div"]:
        text = element.get_text(strip=True)
        if text:
            text_parts.append(text)

# Datum/Zeitstempel
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Schreibe alles in eine Textdatei
output_file = f"matchdetails_{timestamp}.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(text_parts))

print(f"Datei gespeichert: {output_file}")