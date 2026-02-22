from src.pipeline import main
import tkinter as tk
from tkinter import simpledialog, messagebox

if __name__ == "__main__":

    root = tk.Tk()
    root.withdraw()

    # Mostra um pop-up para o usuário digitar algo
    user_input = simpledialog.askstring("Sender", "Para confirmar o envio digite send:")

    # Mostra o que foi digitado
    if user_input == "send":
        
        messagebox.showinfo(title="Sender",message="Envio confirmado!")
        main(EXECUTION_MODE="production", SAFE_TO_SEND=1, SAVE_MATCH= 1)
    else:
        messagebox.showwarning("Aviso", "A palavra digitada não foi send, cancelando o envio")

    end_task = simpledialog.askstring("Sender", "Para finalizar a tarefa digite end:")