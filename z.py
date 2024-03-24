import streamlit as st
import os
from PIL import Image as PILImage
from natsort import natsorted
import chess.pgn
import chess.svg
import io
from wand.image import Image
import matplotlib.pyplot as plt
import pandas as pd
import re
import shutil

def clearing():
    shutil.rmtree('chess_moves')
    shutil.rmtree('chess_moves_png')

class ChessVisualizationApp:
    def __init__(self):
        self.directory = 'chess_moves'
        self.png_directory = 'chess_moves_png'

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        if not os.path.exists(self.png_directory):
            os.makedirs(self.png_directory)

    def save_svg(self, pgn):
        game = chess.pgn.read_game(io.StringIO(pgn))

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        board = chess.Board()

        for move_number, move in enumerate(game.mainline_moves(), start=1):
            board.push(move)
            svg_board = chess.svg.board(board=board)
            file_name = os.path.join(self.directory, f'chess_move_{move_number}.svg')
            with open(file_name, 'w') as f:
                f.write(svg_board)

        self.batch_convert_svg_to_png(self.directory, self.png_directory)

    def convert_svg_to_png(self, svg_path, output_folder):
        os.makedirs(output_folder, exist_ok=True)
        svg_filename = os.path.splitext(os.path.basename(svg_path))[0]
        png_path = os.path.join(output_folder, f"{svg_filename}.png")

        with Image(filename=svg_path, format="svg") as img:
            img.format = "png"
            img.save(filename=png_path)

    def batch_convert_svg_to_png(self, input_folder, output_folder):
        svg_files = [file for file in os.listdir(input_folder) if file.endswith(".svg")]
        for svg_file in svg_files:
            svg_path = os.path.join(input_folder, svg_file)
            self.convert_svg_to_png(svg_path, output_folder)

    def run(self):

        st.title("Chess Visualization App")
        pgn = st.text_area("Paste PGN here:", height=10)

        if st.button("Save SVG"):
            self.save_svg(pgn)
            st.success("SVG files saved and converted to PNG in the 'chess_moves_png' directory.")

        # Get the list of image paths
        image_paths = [os.path.join(self.png_directory, file) for file in natsorted(os.listdir(self.png_directory))
                   if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]


        if not image_paths:
            st.warning("No PNG images found. Please save SVG files first.")

        else:
            current_index = st.session_state.get("current_index", 0)
            # Create an empty container to hold the image
            image_container = st.empty()
            display_image(image_container, image_paths, current_index)

            if st.button("Show Previous"):
                show_previous(image_container, image_paths, current_index)

            if st.button("Show Next"):
                show_next(image_container, image_paths, current_index)

def display_image(container, image_paths, current_index):
    if image_paths:
        image_path = image_paths[current_index]
        image = PILImage.open(image_path)
        image.thumbnail((500, 500))

        # Display the image within the container
        container.image(image, caption=f"Image {current_index + 1}/{len(image_paths)}", use_column_width=500)

def show_previous(container, image_paths, current_index):
    if image_paths:
        current_index = (current_index - 1) % len(image_paths)
        st.session_state["current_index"] = current_index
        display_image(container, image_paths, current_index)

def show_next(container, image_paths, current_index):
    if image_paths:
        current_index = (current_index + 1) % len(image_paths)
        st.session_state["current_index"] = current_index
        display_image(container, image_paths, current_index)

def calculate_accuracy(move_sequence):
        white_moves, black_moves = move_sequence[0::2], move_sequence[1::2]
        white_accuracy = [sum(1 for move in white_moves[:i+1] if re.search(r'[+#]', move)) / (i+1) for i in range(len(white_moves))]
        black_accuracy = [sum(1 for move in black_moves[:i+1] if re.search(r'[+#]', move)) / (i+1) for i in range(len(black_moves))]
        return white_accuracy, black_accuracy


class GameVisualizationAPP:
    def load_data(self,file_path):
        return pd.read_csv(file_path)

    def calculate_accuracy(move_sequence):
        white_moves, black_moves = move_sequence[0::2], move_sequence[1::2]
        white_accuracy = [sum(1 for move in white_moves[:i+1] if re.search(r'[+#]', move)) / (i+1) for i in range(len(white_moves))]
        black_accuracy = [sum(1 for move in black_moves[:i+1] if re.search(r'[+#]', move)) / (i+1) for i in range(len(black_moves))]
        return white_accuracy, black_accuracy

    def plot_time_taken(self,data):
        white_time = [time.split(':') for time in data['white_time']]
        black_time = [time.split(':') for time in data['black_time']]
    
        white_seconds = [int(h) * 3600 + int(m) * 60 + int(s) for h, m, s in white_time]
        black_seconds = [int(h) * 3600 + int(m) * 60 + int(s) for h, m, s in black_time]
    
        move_numbers = list(range(1, (len(data) + 1)))

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(move_numbers, white_seconds, label='White Player', marker='o', linestyle='-', color='b')
        ax.plot(move_numbers, black_seconds, label='Black Player', marker='s', linestyle='--', color='r')

        ax.set_xlabel('Move Number')
        ax.set_ylabel('Time (seconds)')
        ax.set_title('Time Taken by Each Player for Each Move')
        ax.legend()
        ax.grid()

        st.pyplot(fig)

    def plot_pieces_captured(self,data):
        captured_pieces_white = [0]
        captured_pieces_black = [0]
        moves = [0]

        for _, row in data.iterrows():
            white_move, black_move = row['white_move'], row['black_move']
            white_captured = white_move.count('x')
            black_captured = black_move.count('x')

            captured_pieces_white.append(captured_pieces_white[-1] + white_captured)
            captured_pieces_black.append(captured_pieces_black[-1] + black_captured)

            moves.append(moves[-1] + 1)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(moves, captured_pieces_white, label="White", marker='o')
        ax.plot(moves, captured_pieces_black, label="Black", marker='s')

        ax.set_xlabel("Move Number")
        ax.set_ylabel("Pieces Captured")
        ax.legend()
        ax.set_title("Pieces Captured by Each Player vs. Move Number")
        ax.grid()

        st.pyplot(fig)


    def plot_accuracy(self,data):
        move_sequence = [data.iloc[i, 0:2].values for i in range(len(data))]
        white_accuracy, black_accuracy = calculate_accuracy([move for moves in move_sequence for move in moves])

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(range(1, len(white_accuracy) + 1), white_accuracy, label='White Player Accuracy')
        ax.plot(range(1, len(black_accuracy) + 1), black_accuracy, label='Black Player Accuracy')
        ax.set_xlabel('Move Number')
        ax.set_ylabel('Accuracy')
        ax.set_title('Player Accuracy Over Time')
        ax.legend()
        ax.grid()

        st.pyplot(fig)

    def plot_time_difference(self,data):
        data['white_time'] = pd.to_timedelta(data['white_time']).dt.total_seconds()
        data['black_time'] = pd.to_timedelta(data['black_time']).dt.total_seconds()

        data['time_diff_white'] = data['white_time'].diff()
        data['time_diff_black'] = data['black_time'].diff()

        fig, ax = plt.subplots()
        ax.plot(data.index + 1, data['time_diff_white'], label='White', marker='o')
        ax.plot(data.index + 1, data['time_diff_black'], label='Black', marker='o')
        ax.set_title('Time Difference Between Moves')
        ax.set_xlabel('Move Number')
        ax.set_ylabel('Time Difference (seconds)')
        ax.legend()
        ax.grid()

        st.pyplot(fig)

    def plot_average_move_time(self,data):
        data['white_time'] = pd.to_timedelta(data['white_time'])
        data['black_time'] = pd.to_timedelta(data['black_time'])

        data['avg_move_time_white'] = data['white_time'].cumsum() / (data.index + 1)
        data['avg_move_time_black'] = data['black_time'].cumsum() / (data.index + 1)

        fig, ax = plt.subplots()
        ax.plot(data.index + 1, data['avg_move_time_white'].dt.total_seconds(), label='White', marker='o')
        ax.plot(data.index + 1, data['avg_move_time_black'].dt.total_seconds(), label='Black', marker='o')
        ax.set_title('Average Move Time by Player')
        ax.set_xlabel('Move Number')
        ax.set_ylabel('Average Move Time (seconds)')
        ax.legend()
        ax.grid()

        st.pyplot(fig)

    def run(self, st):
        st.title("Chess Analysis Web App")

        # Upload CSV file
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        if uploaded_file is not None:
            # Load data
            data = self.load_data(uploaded_file)

            # Display the data
            st.write("## Chess Data")
            st.write(data)

            # Plot time taken
            st.write("## Time Taken by Each Player for Each Move")
            self.plot_time_taken(data)

            # Plot pieces captured
            st.write("## Pieces Captured by Each Player vs. Move Number")
            self.plot_pieces_captured(data)

            # Plot accuracy
            st.write("## Player Accuracy Over Time")
            self.plot_accuracy(data)

            # Plot time difference
            st.write("## Time Difference Between Moves")
            self.plot_time_difference(data)

            # Plot average move time
            st.write("## Average Move Time by Player")
            self.plot_average_move_time(data)
        

if __name__ == "__main__":
    #clearing()
    
    option = st.sidebar.selectbox("Select App", ["Chess Visualization","GameVisualization"])

    if option == "Chess Visualization":
        chess_app = ChessVisualizationApp()
        chess_app.run()

    if option == "GameVisualization":
        gv = GameVisualizationAPP()
        gv.run(st)
