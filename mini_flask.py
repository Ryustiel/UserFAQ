from flask import Flask, render_template

app = Flask(__name__)

# chargement direct du css
# (plutôt que de passer par des fichiers statiques pour éviter les bugs)
with open("static/style.css", "r") as f:
    STYLESHEET = f.read()

with open("static/script.js", "r") as f:
    SCRIPT = f.read()

class IDManager():
    def __init__(self):
        self.key = 0
    def get_id(self):
        self.key += 1
        return self.key

def get_box(ids):
    s = f"""
    <button class=box id=button{ids.get_id()}>
        <div style='background-color: orange; width: 100px; height: 100px;'>
        </div>
        <p>
            Example text with <a href="https://www.google.com" target=_blank>link</a>
        </p>
    </button>
    """
    return s

def get_grid(count, ids):
    s = ""
    for _ in range(count):
        s += get_box(ids)
    return s

@app.route('/')
def hello():
    ids = IDManager()
    return render_template(
        "main.html", 
        stylesheet = STYLESHEET, 
        script = SCRIPT,
        grid = get_grid(5, ids)
    )

if __name__ == '__main__':
    app.run(debug=True)