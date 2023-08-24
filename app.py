import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from json import loads
from os import listdir

# LOADING FILES

with open("static/streamlit.css", "r") as f:
    CUSTOM_STYLE = f"<style>{f.read()}</style>"

with open("static/script.js", "r") as f:
    CUSTOM_SCRIPT = f"<script>{f.read()}</script>"

with open("vignettes.json", "r", encoding="utf-8") as f:
    content = f.read()
    TUTORIAL_DATA = loads(content)

CSS_OPTION_CONTAINER = """
    {
    background-color: none;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(10px, 1fr)); 
    gap: 20px;
    }
"""

CSS_NODE_CONTAINER = """
    {
    background-color: #333; /* Dark gray */
    }
"""

def scroll_to(target):
    # Define the scroll operation as a function and pass in something unique for each
    # page load that it needs to re-evaluate where "bottom" is
    js = """
    <script>
        function scroll(target_id){
            var element = document.getElementById(target_id);
            element.scrollIntoView({behavior: "smooth"});
        }
        scroll("%s")
    </script>
    """

    #raise ValueError(f"Attempting to insert {js % target}")

    st.markdown(js % target, unsafe_allow_html=True)


def clear_image_path(path):
    """
    ajoute le prefixe de dossier,
    cherche dans le dossier images si une image porte ce nom avec
    les extensions usuelles (png, jpg, ...).
    Si c'est le cas ajoute l'extension associée.
    Retourne toujours le chemin images/path sans extension ajoutée sinon.
    """
    dir_content = listdir("images/")
    for extension in ["", ".png", ".jpg", ".jpeg"]:
        if path + extension in dir_content:
            path = path + extension
            break

    return "images/" + path

# INTERFACE

class KeyManager():
    """
    Simple compteur qui s'auto incremente
    pour delivrer un identifiant unique 
    a chaque element de l'interface.
    """
    def __init__(self, starting_id = 0):
        self.key = starting_id
    def get_key(self):
        self.key += 1
        return self.key

class Node():
    """
    Correspond a un element instructif de l'interface.
    """
    def __init__(self):
        self.title = ""
        self.message = ""
        self.image = None
        self.options = [] # Options
    def get_option(self, option_id):
        return self.options[option_id]
    
    def render(self, show_options=False):
        container = stylable_container(
            key = f"node_container_{self.title.replace(' ', '_')}",
            css_styles=CSS_NODE_CONTAINER
        )
        with container:
            st.markdown(f"<h2>{self.title}</h2>", unsafe_allow_html=True)
            st.write(self.message, key = self.title)
            if self.image is not None:
                st.image(self.image, use_column_width=True)
        
        definitive_result = (False, None, None) # default result = no button pressed 
        if show_options:
            if len(self.options) > 0: # there are buttons to be displayed
                option_container = stylable_container(
                    key = f"option_container_{self.title.replace(' ', '_')}", 
                    css_styles = CSS_OPTION_CONTAINER
                    )
                # create all o the buttons
                # and keep track of whether they were pressed or not
                for option_id, option in enumerate(self.options):
                    result = option.render(option_container, self.title, option_id)
                    
                    # only one button can be pressed at a time
                    # definitive_result keeps track of pressed buttons if there is any
                    if result[0] == True:
                        definitive_result = result
        else:
            with container: # on ajoute un bouton de retour en arriere
                clicked = st.button("Revenir ici", key=f"backwards_{self.title.replace(' ', '_')}")
                if clicked:
                    definitive_result = True, self.title, -1
                    # option_id == -1 triggers the regular option display
            with stylable_container(
                key = f"selected_option_container_{self.title.replace(' ', '_')}",
                css_styles = "{background-color: none;}"
            ):
                option = self.options[st.session_state['selected_option'][self.title]] # fetch selected option object
                st.text(option.title)


        return definitive_result

class Option():
    """
    Correspond aux boutons de l'interface.
    """
    def __init__(self):
        self.title = ""
        self.image = None
        self.target = None # Node Object
        self.retour = [] # Nodes to jump back to
    def render(self, container, node_name, option_id):
        with container:
            key = f"{option_id}:node{node_name}"
            clicked = st.button(self.title, key=key)
            if clicked:
                return True, node_name, option_id
            else:
                return False, None, None

class OptionGraph():
    """
    Interprete le fichier vignettes.json en une arborescence simple.
    Est une interface pour afficher des objets Option et Node
    en fonction de la saisie utilisateur qui lui est transmise. 
    """
    def __init__(self):
        self.nodes = {}

        self.import_tutorial()
        
    def current_node(self) -> str:
        if len(st.session_state['history']) == 0:
            return None
        else:
            return st.session_state['history'][-1]
        
    def run_option(self, node_name, option_id):
        assert option_id != -1
        node = self.nodes[node_name]
        option = node.get_option(option_id)
        # attempts to move backwards (retour)
        if option.retour != []:
            for rt in option.retour:
                # recherche parmi les nodes de l'historique
                for i, node_name_history in enumerate(st.session_state['history']):
                    
                    # considere rt comme un nom de node
                    if node_name_history == rt:
                        if i != len(st.session_state['history']) - 1:
                            # removing entries prior to this node
                            for j in range(len(st.session_state['history']) - 1, i, -1):
                                st.session_state['history'].pop(j)
                        # now last node in history
                        scroll_to(node_name) # SCROLLS BACK TO THE OPTION
                        return # job done
                    
                    # considere rt comme un nom d'option
                    # recherche parmi les options de chaque node de history
                    for option_id_history, option in enumerate(self.nodes[node_name_history].options):
                        if option.title == rt:
                            # se deplace automatiquement vers cette option
                            self.button_clicked(node_name_history, option_id_history)
                            return

        # attemps to move to target
        if option.target is not None:
            target = option.target
            if target not in self.nodes.keys():
                raise ValueError("""
                    Dans le fichier vignettes.json, 
                    vous avez mis une destination (prochain) invalide.
                    Regardez dans la rubrique "{node_name}", c'est 
                    l'option "{target}" qui pose problème : elle ne correspond
                    à aucune rubrique existante. Il y a peut être une erreur de typo.
                    """)
            else: # on est garanti que target existe
                st.session_state['history'].append(target)
                return
                # raise ValueError(f"History is now {str(st.session_state['history'])}")

    def button_clicked(self, node_name=None, option_id=None):
        """
        Updates the graph based on the clicked button.
        """
        # if the button is registered in the history
        # rolls back to this point
        for i, node_name_history in enumerate(st.session_state['history']):
            if node_name_history == node_name:
                if i != len(st.session_state['history']) - 1:
                    # removing entries posterior to this node
                    for j in range(len(st.session_state['history']) - 1, i, -1):

                        st.session_state['history'].pop(j)
                # now last node in history
                st.session_state['selected_option'][node_name] = option_id

                if option_id != -1:  
                    self.run_option(node_name, option_id)
                st.experimental_rerun()
                return # job done
        
        # node not in history, could be an artefact
        # executes the node option nonetheless
        current_node = self.current_node()
        if current_node is not None:
            st.session_state['selected_option'][current_node] = option_id
        self.run_option(node_name, option_id)
        return
        
    def update_loop(self):
        is_button_clicked, node_name, option_id = self.render()
        if is_button_clicked:
            self.button_clicked(node_name, option_id)

    def render(self):
        """
        renders the buttons
        AND keeps track of which one is pressed.
        """
        # default : no button pressed
        definitive_result = (False, None, None)

        last_one = len(st.session_state['history']) - 1
        for i, node_name in enumerate(st.session_state['history']):
            
            node = self.nodes[node_name]
            
            if i == last_one:
                result = node.render(show_options=True)
            else:
                result = node.render()
            # SI LES VIGNETTES NE SONT PAS LES BONNES,
            # VERIFIER SI ENUMERATE INCREMENTE A PARTIR DE ZERO
            # OU A PARTIR DE 1

            if result[0] == True:
                definitive_result = result
        
        return definitive_result

    def import_tutorial(self):
        """
        unpacks TUTORIAL_DATA en une arborescence
        """
        self.nodes = {} # file
        
        for title, content in TUTORIAL_DATA.items():

            # brand new node entry
            if not title in st.session_state['selected_option'].keys():
                st.session_state['selected_option'][title] = -1

            new_node = Node()
            
            new_node.title = title

            if 'texte' in content.keys():
                new_node.message = content['texte']

            if 'image' in content.keys():
                new_node.image = clear_image_path(content['image'])
        
            self.nodes[title] = new_node
        
        for title, content in TUTORIAL_DATA.items():
            if 'options' in content.keys():

                for name, content in content['options'].items():
                    # content est un dictionnaire de paramètres d'options
                    new_option = Option()
                    new_option.title = name
                    if 'prochain' in content.keys():
                        if content['prochain'] in self.nodes.keys():
                            # l'option existe, on peut l'ajouter
                            new_option.target = content['prochain']
                        else:
                            # replacing name to display error messages
                            new_option.name = f"Le nom {content['prochain']} n'est psa valide"

                    if 'retour' in content.keys():
                        new_option.retour = content['retour']

                    if 'image' in content.keys():
                        new_option.image = clear_image_path(content['image'])

                    self.nodes[title].options.append(new_option)


def main():

    st.markdown(CUSTOM_STYLE, unsafe_allow_html=True)
    st.markdown(CUSTOM_SCRIPT, unsafe_allow_html=True)

    container = st.container()

    with container:
        graph.update_loop()

    scroll_to(st.session_state['history'][-1])
    

if __name__ == "__main__":

    root = "Première idée du problème"

    if not "history" in st.session_state:
        st.session_state['history'] = [root]

    if not "selected_option" in st.session_state:
        st.session_state['selected_option'] = {}

    graph = OptionGraph()

    main()