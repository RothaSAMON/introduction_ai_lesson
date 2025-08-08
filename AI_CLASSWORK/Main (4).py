import tkinter as tk
import random
from tkinter import messagebox

class ColorMatchingGame:
    def __init__(self, master):
        self.master = master
        master.title("CSP Color Matching Game")
        master.geometry("400x450") # Set a fixed window size
        master.resizable(False, False) # Disable resizing

        self.colors = ["red", "orange", "yellow", "purple", "blue", "green", "brown", "white", "gray"]
        self.current_grid_colors = []
        self.selected_indices = []
        self.matched_colors_count = 0

        # --- Game UI Frame ---
        self.game_frame = tk.Frame(master, bd=2, relief="groove", padx=10, pady=10)
        self.game_frame.pack(pady=20)

        self.color_buttons = []
        for i in range(3):
            row_buttons = []
            for j in range(3):
                button = tk.Button(self.game_frame, width=8, height=4,
                                   command=lambda r=i, c=j: self.on_button_click(r, c))
                button.grid(row=i, column=j, padx=5, pady=5)
                row_buttons.append(button)
            self.color_buttons.append(row_buttons)

        # --- Message Label ---
        self.message_label = tk.Label(master, text="Click 'New Game' to start!", font=("Arial", 12))
        self.message_label.pack(pady=10)

        # --- Control Buttons Frame ---
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(pady=10)

        self.check_button = tk.Button(self.control_frame, text="Check Matching", command=self.check_matching)
        self.check_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = tk.Button(self.control_frame, text="Clear", command=self.clear_selection)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.new_game_button = tk.Button(self.control_frame, text="New Game", command=self.new_game)
        self.new_game_button.pack(side=tk.LEFT, padx=5)

        self.new_game() # Start a new game automatically on launch

    def new_game(self):
        self.current_grid_colors = random.sample(self.colors, len(self.colors))
        self.selected_indices = []
        self.matched_colors_count = 0
        self.message_label.config(text="Select colors to match!")
        self.update_grid()
        self.enable_all_buttons()
        self.reset_button_borders()

    def update_grid(self):
        for i in range(3):
            for j in range(3):
                color_index = i * 3 + j
                color = self.current_grid_colors[color_index]
                self.color_buttons[i][j].config(bg=color, state=tk.NORMAL) # Set background color

    def on_button_click(self, row, col):
        index = row * 3 + col
        if index not in self.selected_indices:
            self.selected_indices.append(index)
            # Add a visual indicator for selection (e.g., a thicker border)
            self.color_buttons[row][col].config(relief="solid", bd=3)
        else:
            self.selected_indices.remove(index)
            # Remove the visual indicator
            self.color_buttons[row][col].config(relief="raised", bd=2) # Default border

    def check_matching(self):
        if len(self.selected_indices) == 0:
            self.message_label.config(text="Please select colors first!")
            return

        # Simple matching: Check if the selected colors are in their original shuffled order
        # This is a basic example. You can implement more complex matching rules here.
        # For instance, if you want to match pairs of the same color, you'd need to
        # generate duplicate colors in self.colors and then check pairs.

        # For this example, let's say the goal is to select colors in an ascending order
        # of their initial shuffled position.
        # This is a very simple "memory" like game.
        # Let's redefine the goal: User has to select colors in the order they appear in the *original* self.colors list.
        # This means the game is about remembering the fixed order and picking them from the shuffled grid.
        # Get the actual colors of the selected buttons based on their original position in the self.colors list
        # This is a simplified matching where we are trying to find colors in a specific sequence (the order of self.colors)
        # from the shuffled grid.
        
        # A more common matching game would be to find pairs of identical colors, or match color names to colors.
        # For demonstration purposes, let's make it a "find all the colors in the original list" game.

        correct_selection_count = 0
        for selected_idx in self.selected_indices:
            selected_color_name = self.current_grid_colors[selected_idx]
            if selected_color_name in self.colors: # Check if the color is one of our base colors
                correct_selection_count += 1
        
        if correct_selection_count == len(self.selected_indices) and len(self.selected_indices) == len(self.colors):
            self.message_label.config(text="Congratulations! All colors matched!")
            self.disable_all_buttons()
            messagebox.showinfo("Game Over", "You matched all colors!")
        elif correct_selection_count > 0:
            self.message_label.config(text=f"You've matched {correct_selection_count} out of {len(self.colors)} potential colors. Keep going!")
        else:
            self.message_label.config(text="No new matches found. Try again!")

    def clear_selection(self):
        self.selected_indices = []
        self.reset_button_borders()
        self.message_label.config(text="Selection cleared.")

    def reset_button_borders(self):
        for i in range(3):
            for j in range(3):
                self.color_buttons[i][j].config(relief="raised", bd=2) # Reset to default

    def disable_all_buttons(self):
        for i in range(3):
            for j in range(3):
                self.color_buttons[i][j].config(state=tk.DISABLED)

    def enable_all_buttons(self):
        for i in range(3):
            for j in range(3):
                self.color_buttons[i][j].config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    game = ColorMatchingGame(root)
    root.mainloop()