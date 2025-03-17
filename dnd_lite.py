import random
import google.generativeai as genai
import os
import tkinter as tk
from tkinter import ttk, scrolledtext

# Google Gemini API configuration
os.environ["GEMINI_API_KEY"] = "AIzaSyCr9oOQne6hVZ1rNg5PaXmklIN-z4tcA5Q"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Race and Weapon Data
race_data = {
    "Human": {"HP": 100, "Weapons": ["Sword", "Spear", "Bow"]},
    "Elf": {"HP": 100, "Weapons": ["Longbow", "Dagger", "Rapier"]},
    "Dwarf": {"HP": 100, "Weapons": ["Axe", "Hammer", "Crossbow"]},
    "Orc": {"HP": 100, "Weapons": ["Dagger", "Shortsword", "Sling"]},
    "Mage": {"HP": 100, "Weapons": ["Staff", "Wand", "Orb"]},
}

character_names = ["Kharmor", "Muriggs", "Bentharm", "Grandohr", "Ranmur"]




class CharacterSelection:
    def __init__(self, root, start_game_callback):
        self.root = root
        root.resizable(False, False)
        self.start_game_callback = start_game_callback
        self.characters = []

        self.root.title("Character Customization")
        self.root.geometry("400x600")

        self.frame = tk.Frame(root)
        self.frame.pack()

        self.character_data = {}

        for name in character_names:
            label = tk.Label(self.frame, text=name)
            label.pack()

            race_var = tk.StringVar()
            race_menu = ttk.Combobox(self.frame, textvariable=race_var, values=list(race_data.keys()), state="readonly")
            race_menu.pack()

            weapon_var = tk.StringVar()
            weapon_menu = ttk.Combobox(self.frame, textvariable=weapon_var, state="readonly")
            weapon_menu.pack()

            # Store references correctly for each character
            self.character_data[name] = {
                "race_var": race_var,
                "weapon_var": weapon_var,
                "weapon_menu": weapon_menu,  # Store a reference to each weapon menu
            }

            # Bind event to update only the respective character's weapon choices
            race_menu.bind("<<ComboboxSelected>>", lambda event, n=name: self.update_weapons(n))

        self.confirm_button = tk.Button(self.frame, text="Confirm Party", command=self.confirm_party)
        self.confirm_button.pack()

    def update_weapons(self, character_name):
        """Updates weapon choices for the respective character only"""
        selected_race = self.character_data[character_name]["race_var"].get()
        if selected_race:
            weapons = race_data[selected_race]["Weapons"]
            weapon_menu = self.character_data[character_name]["weapon_menu"]
            weapon_menu["values"] = weapons
            weapon_menu.set(weapons[0])  # Auto-select first weapon

    def confirm_party(self):
        """Confirms the character selection and starts the game"""
        self.characters = []
        for name in character_names:
            race = self.character_data[name]["race_var"].get()
            weapon = self.character_data[name]["weapon_var"].get()
            if race and weapon:
                hp = race_data[race]["HP"]
                self.characters.append({"name": name, "race": race, "weapon": weapon, "HP": hp, "MaxHP": hp})

        if len(self.characters) == len(character_names):
            self.frame.destroy()
            self.start_game_callback(self.characters)
        else:
            messagebox.showerror("Error", "Please select race and weapon for all characters.")



class DnDGame:
    def __init__(self, root, characters):
        self.root = root
        root.resizable(False, False)
        self.root.title("D&D Lite Adventure")
        self.characters = characters
        self.turn = 0
        self.previous_turns = []
        self.context = self.get_party_context()

        self.label = tk.Label(root, text="Welcome to D&D Lite! Click 'Roll Dice' to start.")
        self.label.pack()

        self.text_area = scrolledtext.ScrolledText(root, width=60, height=20)
        self.text_area.pack()

        self.roll_button = tk.Button(root, text="Roll Dice", command=self.play_turn)
        self.roll_button.pack()

        self.quit_button = tk.Button(root, text="Quit", command=root.destroy)
        self.quit_button.pack()

        self.update_text("Game started! Prepare for your adventure.\n\n" + self.context)

    def roll_die(self):
        return random.randint(1, 20)

    def generate_story(self, rolls):
        question = (
            f"Turn {self.turn}: The party encounters a challenge! Based on their current situation:\n"
            f"{self.context}\n"
            f"Previous Turns:\n"
            f"{chr(10).join(self.previous_turns)}\n"
            f"Each character rolled their own die: {', '.join([f'{char['name']} rolled {roll}' for char, roll in zip(self.characters, rolls)])}.\n"
            f"Describe what happens next based on these rolls, including how the enemies attack each character and the effects of those attacks. If the character/enemy rolled 16-20, they do 35-55 damage to their opponent. A roll of 16 does 35 damage, a roll of 17 does 40 damage, a roll of 18 does 45 damage, a roll of 19 does 50 damage, a roll of 20 does 55 damage. If they rolled 5-15, they do 10-30 damage to their opponent. A roll of 5 does 10 damage, a roll of 6 does 12 damage, a roll of 7 does 14 damage, a roll of 8 does 16 damage, a roll of 9 does 18 damage, a roll of 10 does 20 damage, a roll of 11 does 22 damage, a roll of 12 does 24 damage, a roll of 13 does 26 damage, a roll of 14 does 28 damage, a roll of 15 does 30 damage. If they rolled 1-4, they do 0-9 damage. A roll of 1 does 0 damage, a roll of 2 does 3 damage, a roll of 3 does 6 damage, a roll of 4 does 9 damage. If a character is dead, ignore their dice roll. Assume there are 5 enemies each with 100 HP, and each character can go for an enemy of their choosing during their turn (the enemies will be named enemy 1-5). Each enemy can go for a character of their choosing during their turn unless that character is dead, and visa versa. At the end of each turn, give the current HP of each enemy and character. Once either all the heroes or enemies are dead, tell the user that the battle is over."
        )
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(question)

            return response.text
        except Exception as e:
            return f"Error with Gemini API: {e}"

    def get_party_context(self):
        return "\n".join(
            [f"{char['name']} the {char['race']} wielding a {char['weapon']} with {char['HP']} HP." for char in
             self.characters])

    def play_turn(self):
        self.turn += 1
        rolls = [self.roll_die() for _ in self.characters]
        self.update_text(f"\n--- Turn {self.turn} ---\n")
        for char, roll in zip(self.characters, rolls):
            self.update_text(f"{char['name']} rolled a {roll}!")

        story = self.generate_story(rolls)
        self.update_text(f"\nStory for Turn {self.turn}:\n{story}")
        self.previous_turns.append(f"Turn {self.turn}: {story}")
        self.context = self.get_party_context()

        if "the battle is over" in story.lower():
            self.roll_button.pack_forget()

    def update_text(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.yview(tk.END)


def main():
    root = tk.Tk()

    def start_game(characters):
        root.destroy()
        new_root = tk.Tk()
        DnDGame(new_root, characters)
        new_root.mainloop()

    CharacterSelection(root, start_game)
    root.mainloop()


if __name__ == "__main__":
    main()
